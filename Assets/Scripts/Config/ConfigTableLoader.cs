using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

// 구글 시트 ConfigTable(공통 설정값)을 받아 키로 조회한다
// 값은 시트 ValueType 열에 맞춰 object로 담고, Get<T>에서 요청한 타입으로 꺼낸다
// 게임 시작 시 스스로 로드한다. 로드 전, 키가 없을 때, 타입이 맞지 않을 때는 fallback 값을 돌려준다

// object로 담아 박싱 비용이 있지만, 출시 때는 시트값을 csv로 굽거나 상수화할 예정이므로 기획 편의성을 우선한다
public static class ConfigTableLoader
{
    const string SheetUrl = "https://docs.google.com/spreadsheets/d/1Rakb-IC_AwaCy93-ioBw9UIesSYxOdWwIFE4Kwc_UB8/export?format=csv&gid=0"; // ConfigKey, Description, ValueType, Value, Unit, BalanceIntent

    static readonly Dictionary<string, object> configs = new();
    public static bool IsLoaded { get; private set; }
    public static event Action Loaded;

    static string CachePath => $"{Application.persistentDataPath}/config_table.csv";

    public static T Get<T>(string key, T fallback)
    {
        if (!configs.TryGetValue(key, out object value)) return fallback;
        if (value is T typed) return typed;

        // 시트 타입과 요청 타입이 달라도 숫자끼리는 변환한다 (Int 값을 float로 읽기 등)
        try {
            return (T)Convert.ChangeType(value, typeof(T), CultureInfo.InvariantCulture);
        }
        catch (Exception e) when (e is InvalidCastException || e is FormatException || e is OverflowException) {
            Debug.LogWarning($"[ConfigTableLoader] {key} 값 {value}({value.GetType().Name})을 {typeof(T).Name}으로 읽을 수 없음, fallback 사용");
            return fallback;
        }
    }

    public static bool Has(string key) => configs.ContainsKey(key);


    // 로드

    // 시트 다운로드, 실패하면 마지막 캐시 사용. 플레이 중 다시 부르면 시트 수정분을 바로 반영한다
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    public static void Load()
    {
        configs.Clear();
        IsLoaded = false;

        var request = UnityWebRequest.Get(SheetUrl);
        request.SendWebRequest().completed += _ =>
        {
            string csv = null;
            if (request.result == UnityWebRequest.Result.Success) {
                csv = request.downloadHandler.text;
                File.WriteAllText(CachePath, csv, Encoding.UTF8);
            }
            else if (File.Exists(CachePath)) {
                Debug.LogWarning($"[ConfigTableLoader] 다운로드 실패: {request.error}, 캐시 사용");
                csv = File.ReadAllText(CachePath, Encoding.UTF8);
            }
            else Debug.LogError("[ConfigTableLoader] 다운로드 실패, 캐시도 없음, 기본값으로 동작");
            request.Dispose();

            if (csv != null) Parse(csv);
            IsLoaded = true;
            Debug.Log($"[ConfigTableLoader] 설정값 {configs.Count}개 로드 완료");
            Loaded?.Invoke();
        };
    }

    // ConfigKey 열을 키로, Value 열을 ValueType 열의 타입으로 담는다
    static void Parse(string csv)
    {
        var rows = CsvUtil.ParseCsvRows(csv);
        if (rows.Count == 0) return;
        int colKey = rows[0].IndexOf("ConfigKey"), colType = rows[0].IndexOf("ValueType"), colValue = rows[0].IndexOf("Value");
        if (colKey < 0 || colType < 0 || colValue < 0) { Debug.LogError("[ConfigTableLoader] 헤더를 찾을 수 없음: ConfigKey/ValueType/Value"); return; }

        for (int r = 1; r < rows.Count; r++) {
            var row = rows[r];
            if (row.Count <= Mathf.Max(colKey, colType, colValue)) continue;
            string key = row[colKey].Trim();
            if (key.Length == 0) continue;

            if (TryParseValue(row[colType].Trim(), row[colValue].Trim(), out object value)) configs[key] = value;
            else Debug.LogWarning($"[ConfigTableLoader] {key} 값 '{row[colValue]}'을 {row[colType]}로 읽을 수 없음");
        }
    }

    static bool TryParseValue(string type, string raw, out object value)
    {
        value = null;
        switch (type) {
            case "Int":
                if (!int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out int i)) return false;
                value = i; return true;
            case "Float":
                if (!float.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out float f)) return false;
                value = f; return true;
            case "Bool":
                if (!bool.TryParse(raw, out bool b)) return false;
                value = b; return true;
            default:
                value = raw; return true; // String 등은 문자열 그대로
        }
    }
}
