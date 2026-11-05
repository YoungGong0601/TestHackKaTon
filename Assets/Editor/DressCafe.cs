using System;
using UnityEngine;
using UnityEngine.Rendering;
using static DressKit;

// 카페 방과 거리를 Env_Cafe 하나로 묶어 R2_Cafe 에 넣는다. 다시 돌려도 된다.
// 프리팹 안의 모델은 PH_Map_Cafe.json 과 FillMap 이 넣는다. 인물 모습은 DressStore 가 맡는다.
public static class DressCafe
{
    const float RoadZ = -13f, CrossX = 0.2f, RoadY = -0.14f;   // 도로 중심, 횡단보도, 노면 높이. 보도면이 y 0 이다
    const string Street = "Models/Street/";

    public static void All()
    {
        Art3DTools.Apply();   // 배치 모드에서는 새 FBX 의 재질이 자동으로 연결되지 않는다
        var s = Open("R2_Cafe");   // Open 이 씬을 통째로 바꾸니 묶음은 그 뒤에 만든다
        var env = Root("Env_Cafe");
        Put(env, "Models/PH/PH_CafeRoom__Shell.fbx", "Room", Vector3.zero, Quaternion.identity);
        Road(env);
        SaveEnv(env);
        PutEnv(s, "Env_Cafe");

        // 콜라이더는 프리팹 루트에 있어 그대로 남는다
        Off(s, "Room/Floor", "Room/Ceiling", "Room/Wall_East", "Room/Wall_West", "Room/Wall_Back", "Counter/Wall_BarEnd",
            "Street/Walk_North", "Street/Walk_South", "Street/PH_Road", "Street/PH_Crosswalk",
            "Street/Curb0", "Street/Curb1", "Street/Curb2", "Street/Curb3");

        // 회색 도로 끝선에 있던 난간과 보도 높이의 차를 실제 경계석과 노면에 맞춘다
        Move(s, "Street/Rail0", new Vector3(-12.5f, 0f, RoadZ + 4.09f));
        Move(s, "Street/Rail2", new Vector3(12.7f, 0f, RoadZ + 4.09f));
        Move(s, "Street/Rail1", new Vector3(-12.5f, 0f, RoadZ - 4.09f));
        Move(s, "Street/Rail3", new Vector3(12.7f, 0f, RoadZ - 4.09f));
        Move(s, "Street/Car0", new Vector3(-13f, RoadY, -11f));
        Move(s, "Street/Car1", new Vector3(11f, RoadY, -15f));

        // 버거 포스터라서 꺼 두었던 날개를 숲길 커피 포스터로 켠다
        foreach (var wing in new[] { "PH_Kiosk/Wing_L", "PH_Kiosk/Wing_R" })
        {
            var t = Find(s, wing);
            t.gameObject.SetActive(true);
            Keep(t.gameObject);
        }

        RenderSettings.skybox = Sky();
        Save(s);
    }

    static GameObject Put(Transform parent, string model, string name, Vector3 pos, Quaternion rot) =>
        Place(new Item { model = model, name = name }, parent, pos, rot);

    // 레이아웃의 rotZ 와 같은 뜻이다. 0 이면 모델 앞(-Y)이 -Z 를 본다
    static GameObject Put(Transform parent, string model, Vector3 pos, float rotZ) =>
        Put(parent, Street + model + ".fbx", model, pos, Quaternion.Euler(0f, 180f - rotZ, 0f));

    static void Road(Transform env)
    {
        var ground = Put(env, "Models/LayoutStreet/StreetGround.fbx", "StreetGround", Vector3.zero, Quaternion.Euler(0f, 180f, 0f));
        if (ground != null)
            foreach (var r in ground.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;

        for (int k = -5; k <= 5; k++)
        {
            float x = CrossX + 12f * k;
            string curb = k == 0 ? "StreetCurbRamp" : "StreetCurb", walk = k == 0 ? "StreetSidewalkRamp" : "StreetSidewalk";
            Put(env, k == 0 ? "StreetRoadCrosswalk" : "StreetRoad", new Vector3(x, RoadY, RoadZ), 0f);
            Put(env, curb, new Vector3(x, RoadY, RoadZ + 4f), 0f);
            Put(env, curb, new Vector3(x, RoadY, RoadZ - 4f), 180f);
            Put(env, walk, new Vector3(x, 0f, RoadZ + 6.18f), 0f);
            Put(env, walk, new Vector3(x, 0f, RoadZ - 6.18f), 180f);
            // 모듈 폭 4 m 로 건물까지 닿지 않는다. 겹치는 쪽을 2 mm 낮추고 점자 띠가 위 줄에 가리게 돌린다
            Put(env, "StreetSidewalk", new Vector3(x, -0.002f, -5f), 180f);
            Put(env, "StreetSidewalk", new Vector3(x, -0.002f, -22f), 0f);
        }

        foreach (var x in new[] { -15.5f, 10.5f }) Pole(Put(env, "StreetLight", new Vector3(x, 0f, RoadZ + 4.35f), 0f));
        foreach (var x in new[] { -16.5f, 16.5f }) Pole(Put(env, "StreetLight", new Vector3(x, 0f, RoadZ - 4.35f), 180f));
        Pole(Put(env, "StreetCrosswalkSignal", new Vector3(CrossX + 3.1f, 0f, RoadZ + 4.5f), 0f));
        Pole(Put(env, "StreetCrosswalkSignal", new Vector3(CrossX - 3.1f, 0f, RoadZ - 4.5f), 180f));

        // 도로가 끝나는 곳을 먼 아파트로 막는다. 앞면이 +Z 인 모델이다
        Put(env, "Models/Buildings/BuildingBackdrop.fbx", "Backdrop_W", new Vector3(-72f, 0f, RoadZ), Quaternion.Euler(0f, 90f, 0f));
        Put(env, "Models/Buildings/BuildingBackdrop.fbx", "Backdrop_E", new Vector3(72f, 0f, RoadZ), Quaternion.Euler(0f, -90f, 0f));
    }

    // Unity -batchmode -quit -projectPath . -executeMethod DressCafe.Shots -logFile <로그>  (CAFE_SHOTS=<폴더>)
    public static void Shots()
    {
        var dir = Environment.GetEnvironmentVariable("CAFE_SHOTS");
        var s = Open("R2_Cafe");
        (string name, Vector3 from, Vector3 to)[] views =
        {
            ("street", new(-12f, 1.6f, -20.5f), new(-0.7f, 2.2f, -3f)),
            ("front", new(0.2f, 1.6f, -8f), new(0.2f, 1.8f, -3f)),
            ("door", new(0.2f, 1.6f, -2.3f), new(-1.5f, 1.2f, 2.5f)),
            ("bar", new(-1.5f, 1.6f, 0.6f), new(-2f, 1.3f, 3.5f)),
            ("kiosk", new(1.9f, 1.6f, 2.7f), new(1.9f, 1.3f, 3.82f)),
            ("kiosk_far", new(1.2f, 1.6f, 0.4f), new(1.9f, 1.3f, 3.82f)),
            ("cups", new(-0.1f, 1.45f, 1.7f), new(-0.1f, 1.2f, 2.5f)),
            ("seats", new(0.6f, 1.6f, 0.2f), new(-3f, 0.7f, -2f)),
            ("inside_out", new(-1f, 1.6f, 1.5f), new(-0.7f, 1.4f, -3f)),
        };
        foreach (var v in views)
        {
            Shot(s, v.from, v.to, $"{dir}/cafe_{v.name}.png");   // 첫 장은 임시 프레임이 섞여 나오니 같은 샷을 다시 찍는다
            Shot(s, v.from, v.to, $"{dir}/cafe_{v.name}.png");
        }
    }
}
