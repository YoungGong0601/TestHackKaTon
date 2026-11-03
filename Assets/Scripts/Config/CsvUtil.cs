using System.Collections.Generic;
using System.Text;

// 구글 시트 CSV 내보내기를 행 단위로 나눈다
// 큰따옴표로 감싼 칸 안의 쉼표, 줄바꿈, "" (따옴표 이스케이프)를 처리한다
public static class CsvUtil
{
    public static List<List<string>> ParseCsvRows(string csv)
    {
        var rows = new List<List<string>>();
        var row = new List<string>();
        var cell = new StringBuilder();
        bool inQuotes = false;

        for (int i = 0; i < csv.Length; i++) {
            char c = csv[i];
            if (inQuotes) {
                if (c == '"') {
                    if (i + 1 < csv.Length && csv[i + 1] == '"') { cell.Append('"'); i++; }
                    else inQuotes = false;
                }
                else cell.Append(c);
                continue;
            }

            switch (c) {
                case '"': inQuotes = true; break;
                case ',': row.Add(cell.ToString()); cell.Clear(); break;
                case '\r': break;
                case '\n':
                    row.Add(cell.ToString()); cell.Clear();
                    rows.Add(row); row = new List<string>();
                    break;
                default: cell.Append(c); break;
            }
        }

        // 마지막 줄에 줄바꿈이 없는 경우
        if (cell.Length > 0 || row.Count > 0) {
            row.Add(cell.ToString());
            rows.Add(row);
        }
        return rows;
    }
}
