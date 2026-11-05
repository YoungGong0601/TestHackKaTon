// 영수증 종이. 틈에서 천천히 나와 앞으로 굽었다가 아래로 처지고, 클릭하면 뜯긴다. 원본 hw.js shapeReceipt.
// 내용은 ReceiptCanvas를 Cam_Receipt가 RT_Receipt로 찍은 그림이고, 종이 메시가 그 그림을 스크롤하며 내보낸다.
// 배치: paper = Paper(평소 꺼짐, 원점이 틈), hit = Paper의 콜라이더(KioskSpot id=paper),
//       sheet = Paper/Visual/Sheet의 MeshFilter(재질 Mat_Receipt), cam = KioskRig/Cam_Receipt(평소 꺼짐, target RT_Receipt),
//       body = 메뉴 줄 글자, total = 합계 금액 글자, number = 주문번호 글자 (셋 다 ReceiptCanvas 안)
using TMPro;
using UnityEngine;

public class KioskReceipt : MonoBehaviour
{
    const int Rows = 22;

    [SerializeField] GameObject paper;
    [SerializeField] Collider hit;
    [SerializeField] MeshFilter sheet;
    [SerializeField] Camera cam;
    [SerializeField] TMP_Text body;
    [SerializeField] TMP_Text total;
    [SerializeField] TMP_Text number;

    float show, target, tear, sec;
    Vector3 rest;
    bool restSet;
    Mesh mesh;
    readonly Vector3[] verts = new Vector3[(Rows + 1) * 2];
    readonly Vector2[] uvs = new Vector2[(Rows + 1) * 2];

    static float Length => Bal.G("Kiosk_ReceiptLength", 0.25f);

    public void Print(string lines, string sum, int no, float seconds)
    {
        if (body) body.text = lines;
        if (total) total.text = sum;
        if (number) number.text = no.ToString();
        if (cam) cam.enabled = true;
        if (!paper) return;
        if (!restSet) { rest = paper.transform.localPosition; restSet = true; }
        show = 0f; target = 1f; tear = 0f; sec = Mathf.Max(0.01f, seconds);
        paper.transform.localPosition = rest;
        Shape(0.001f);
        paper.SetActive(true);
    }

    public void CanTear(bool on) { if (hit) hit.enabled = on; }

    public void Tear() { tear = 0.001f; CanTear(false); }

    public void Clear()
    {
        show = target = tear = 0f;
        CanTear(false);
        if (cam) cam.enabled = false;
        if (paper) paper.SetActive(false);
    }

    void OnDestroy() { if (mesh) Destroy(mesh); }

    void Build()
    {
        mesh = new Mesh { name = "ReceiptPaper" };
        mesh.MarkDynamic();
        mesh.vertices = verts;
        mesh.uv = uvs;
        var tris = new int[Rows * 6];
        for (int i = 0; i < Rows; i++)
        {
            int k = i * 2, t = i * 6;
            tris[t] = k; tris[t + 1] = k + 1; tris[t + 2] = k + 2;
            tris[t + 3] = k + 1; tris[t + 4] = k + 3; tris[t + 5] = k + 2;
        }
        mesh.triangles = tris;
        sheet.sharedMesh = mesh;
    }

    /// <summary>나온 길이 L만큼 종이를 편다. 처음은 앞으로, 그다음 아래로 굽고, 다 나오면 위에서 아래로 바로 읽힌다.</summary>
    public void Shape(float L)
    {
        if (!sheet) return;
        if (!mesh) Build();
        float full = Length, half = Bal.G("Kiosk_ReceiptWidth", 0.074f) * 0.5f;
        float bend = Bal.G("Kiosk_ReceiptBendLen", 0.05f), angle = Bal.G("Kiosk_ReceiptBendAngle", 1.45f), r = Bal.G("Kiosk_ReceiptBendRadius", 0.034f);
        for (int i = 0; i <= Rows; i++)
        {
            float s = (float)i / Rows * L;
            float a = Mathf.Min(angle, s / bend * angle);
            float y = s < bend ? -r * (1f - Mathf.Cos(a)) : -r * (1f - Mathf.Cos(angle)) - (s - bend) * Mathf.Sin(angle) - Mathf.Sin(s * 40f) * 0.0008f;
            float z = s < bend ? r * Mathf.Sin(a) : r * Mathf.Sin(angle) + (s - bend) * Mathf.Cos(angle) + Mathf.Sin(s * 22f) * 0.0035f;
            float v = Mathf.Clamp01(1f - (s + full - L) / full);
            int k = i * 2;
            verts[k] = new Vector3(-half, y, -z);       // 손님 쪽이 -Z
            verts[k + 1] = new Vector3(half, y, -z);
            uvs[k] = new Vector2(0f, v);
            uvs[k + 1] = new Vector2(1f, v);
        }
        mesh.vertices = verts;
        mesh.uv = uvs;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
    }

    void Update()
    {
        if (!paper || !paper.activeSelf) return;
        if (show < target && tear <= 0f)
        {
            show = Mathf.MoveTowards(show, target, Time.deltaTime / sec);
            Shape(Mathf.Max(0.001f, show * Length));
            if (show >= target && cam) cam.enabled = false;   // 내용은 RT에 남는다
        }
        if (tear > 0f)
        {
            tear += Time.deltaTime * Bal.G("Kiosk_ReceiptTearRate", 2.4f);
            paper.transform.localPosition = rest + new Vector3(0f, tear * Bal.G("Kiosk_ReceiptTearRise", 0.25f), -tear * Bal.G("Kiosk_ReceiptTearOut", 0.42f));
            if (tear >= 1f) { tear = 0f; paper.SetActive(false); }
        }
    }
}
