using UnityEngine;

// 함정 1종: 폭탄. 재생 중인 차가 닿으면 뒤로 튕겨 내고 사라진다
public class Trap : MonoBehaviour
{
    bool used;

    public static GameObject Create(Vector2 surface, Transform parent)
    {
        var go = new GameObject("Trap");
        go.transform.SetParent(parent);
        go.transform.position = surface + Vector2.up * 0.25f;
        var col = go.AddComponent<CircleCollider2D>();
        col.isTrigger = true;
        col.radius = 0.35f;
        Art.Visual(go.transform, "Trap", new Vector2(0.6f, 0.5f), Color.black, false, 5);
        go.AddComponent<Trap>();
        return go;
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        var car = other.GetComponentInParent<Car>();
        if (used || car == null || car.State != Car.Mode.Play) return;
        used = true; // 차체와 바퀴가 같은 프레임에 닿아도 한 번만
        car.Blast(new Vector2(-Env.Cfg("Trap.ForceX", 4f), Env.Cfg("Trap.ForceY", 6f)));
        Sfx.Play("Trap");
        Destroy(gameObject);
    }
}
