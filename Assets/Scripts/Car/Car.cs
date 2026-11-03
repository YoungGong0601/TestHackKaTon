using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

// 차체 + 바퀴 2개. 녹화 모드에서는 키 입력으로 달리며 입력을 테이프에 쌓고, 재생 모드에서는 테이프대로 달린다
// 재생은 합쳐진 환경에서 한 번만 하므로 녹화 때와 결과가 같을 필요는 없다 (기획서)
public class Car : MonoBehaviour
{
    public enum Mode { Frozen, Record, Play }

    public Mode State { get; private set; }
    public Vector2 Position => body.transform.position;
    public float FlipTime { get; private set; }  // 뒤집힌 채로 지난 시간
    public float StillTime { get; private set; } // 거의 멈춘 채로 지난 시간
    public bool TapeDone => cursor >= tape.Count;
    public float TapeSeconds => tape.Count * Time.fixedDeltaTime;

    Rigidbody2D body;
    readonly Rigidbody2D[] wheels = new Rigidbody2D[2];
    readonly WheelJoint2D[] joints = new WheelJoint2D[2];
    readonly GameObject[,] shapes = new GameObject[2, 4]; // 바퀴별 모양 4종, 하나만 켠다
    readonly List<Vector2> tape = new(); // 고정 프레임마다 (가속, 기울기)
    readonly ContactPoint2D[] contacts = new ContactPoint2D[8];
    PhysicsMaterial2D tire;
    int cursor;
    float wind;

    static readonly Vector2[] anchors = { new(-0.7f, -0.3f), new(0.7f, -0.3f) };
    static readonly Vector2 bodySize = new(2f, 0.5f);

    public static Car Create()
    {
        var car = new GameObject("Car").AddComponent<Car>();
        car.Build();
        return car;
    }

    void Build()
    {
        tire = new PhysicsMaterial2D("Tire") { friction = 1f, bounciness = 0f, frictionCombine = PhysicsMaterialCombine2D.Minimum };

        body = MakeBody("Body", Vector2.zero);
        body.gameObject.AddComponent<BoxCollider2D>().size = bodySize;
        Art.Visual(body.transform, "CarBody", bodySize, new Color(0.85f, 0.25f, 0.2f), false, 10);

        for (int i = 0; i < 2; i++) {
            wheels[i] = MakeBody("Wheel" + i, anchors[i]);
            for (int s = 0; s < 4; s++) shapes[i, s] = MakeShape(wheels[i].transform, (Wheel)s);

            var joint = body.gameObject.AddComponent<WheelJoint2D>();
            joint.connectedBody = wheels[i];
            joint.autoConfigureConnectedAnchor = false;
            joint.anchor = anchors[i];
            joint.connectedAnchor = Vector2.zero;
            joint.suspension = new JointSuspension2D { dampingRatio = 0.7f, frequency = 5f, angle = 90f };
            joints[i] = joint;
        }

        Configure(Wheel.Round, 1f, 1f, 0f);
        Freeze();
    }

    Rigidbody2D MakeBody(string name, Vector2 localPos)
    {
        var go = new GameObject(name);
        go.transform.SetParent(transform, false);
        go.transform.localPosition = localPos;
        var rb = go.AddComponent<Rigidbody2D>();
        rb.interpolation = RigidbodyInterpolation2D.Interpolate;
        return rb;
    }

    GameObject MakeShape(Transform wheel, Wheel kind)
    {
        var go = new GameObject(kind.ToString());
        go.transform.SetParent(wheel, false);
        float size;
        switch (kind) {
            case Wheel.Big:
                size = 1.1f;
                go.AddComponent<CircleCollider2D>().radius = size / 2;
                break;
            case Wheel.Square:
                size = 0.65f;
                go.AddComponent<BoxCollider2D>().size = Vector2.one * size;
                break;
            case Wheel.Star:
                size = 0.9f;
                var star = new Vector2[10];
                for (int k = 0; k < 10; k++) {
                    float a = (90f + k * 36f) * Mathf.Deg2Rad, r = k % 2 == 0 ? size / 2 : size / 4.5f;
                    star[k] = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
                }
                go.AddComponent<PolygonCollider2D>().points = star;
                break;
            default:
                size = 0.7f;
                go.AddComponent<CircleCollider2D>().radius = size / 2;
                break;
        }
        // ponytail: 별 바퀴 플레이스홀더는 원으로 그린다. Wheel_Star 아트가 들어오면 해결
        Art.Visual(go.transform, "Wheel_" + kind, Vector2.one * size, new Color(0.15f, 0.15f, 0.15f), kind != Wheel.Square, 11);
        return go;
    }

    // 재생 전에 환경 적용. 녹화 때는 기본값으로 부른다
    public void Configure(Wheel wheel, float massMul, float tireFriction, float windForce)
    {
        for (int i = 0; i < 2; i++) {
            wheels[i].mass = Env.Cfg("Car.WheelMass", 0.3f);
            for (int s = 0; s < 4; s++) {
                shapes[i, s].SetActive(s == (int)wheel);
                shapes[i, s].GetComponent<Collider2D>().sharedMaterial = null;
            }
        }
        body.mass = Env.Cfg("Car.Mass", 1f) * massMul;
        tire.friction = tireFriction;
        // 머티리얼 값을 바꾼 뒤 다시 넣어야 물리에 반영된다
        foreach (var go in shapes) go.GetComponent<Collider2D>().sharedMaterial = tire;
        wind = windForce;
    }

    public void Teleport(Vector2 pos)
    {
        Place(body, pos);
        for (int i = 0; i < 2; i++) Place(wheels[i], pos + anchors[i]);
        FlipTime = StillTime = 0;
    }

    static void Place(Rigidbody2D rb, Vector2 pos)
    {
        rb.transform.SetPositionAndRotation(pos, Quaternion.identity);
        rb.position = pos;
        rb.rotation = 0;
        rb.linearVelocity = Vector2.zero;
        rb.angularVelocity = 0;
    }

    // 뒤집혔을 때 그 자리에서 바로 세운다
    public void Upright() => Teleport(Position + Vector2.up * 0.5f);

    public void Freeze() => SetMode(Mode.Frozen);

    public void Record()
    {
        tape.Clear();
        SetMode(Mode.Record);
    }

    public void Play()
    {
        cursor = 0;
        SetMode(Mode.Play);
    }

    void SetMode(Mode mode)
    {
        State = mode;
        bool sim = mode != Mode.Frozen;
        body.simulated = sim;
        foreach (var w in wheels) w.simulated = sim;
    }

    public void Blast(Vector2 impulse) => body.AddForce(impulse, ForceMode2D.Impulse);

    void FixedUpdate()
    {
        if (State == Mode.Frozen) return;

        Vector2 input;
        if (State == Mode.Record) tape.Add(input = ReadKeys());
        else input = TapeDone ? Vector2.zero : tape[cursor++];

        float speed = Env.Cfg("Car.MotorSpeed", 500f), torque = Env.Cfg("Car.MotorTorque", 20f);
        foreach (var j in joints) {
            j.useMotor = input.x != 0;
            j.motor = new JointMotor2D { motorSpeed = -input.x * speed, maxMotorTorque = torque }; // 음수가 오른쪽(결승 방향)
        }
        body.AddTorque(input.y * Env.Cfg("Car.TiltTorque", 3f));
        if (State == Mode.Play) body.AddForce(new Vector2(wind, 0));
        body.linearDamping = OnMud() ? Env.Cfg("Surface.MudDrag", 3f) : 0f;

        float dt = Time.fixedDeltaTime;
        FlipTime = Mathf.Cos(body.rotation * Mathf.Deg2Rad) < 0 ? FlipTime + dt : 0;
        StillTime = body.linearVelocity.sqrMagnitude < 0.05f ? StillTime + dt : 0;
    }

    bool OnMud()
    {
        var mud = Track.Materials[(int)Surface.Mud];
        foreach (var w in wheels) {
            int n = w.GetContacts(contacts);
            for (int i = 0; i < n; i++)
                if (contacts[i].collider.sharedMaterial == mud || contacts[i].otherCollider.sharedMaterial == mud) return true;
        }
        return false;
    }

    static Vector2 ReadKeys()
    {
        var k = Keyboard.current;
        if (k == null) return Vector2.zero;
        float x = (k.dKey.isPressed || k.rightArrowKey.isPressed ? 1 : 0) - (k.aKey.isPressed || k.leftArrowKey.isPressed ? 1 : 0);
        float y = (k.wKey.isPressed || k.upArrowKey.isPressed ? 1 : 0) - (k.sKey.isPressed || k.downArrowKey.isPressed ? 1 : 0);
        return new Vector2(x, y);
    }
}
