using System.Collections.Generic;
using UnityEngine.InputSystem;

// 소지품 번호. 화면 표시와 키 입력이 같은 순서를 쓴다. 쪽지(Memo)를 볼 수 있으면 1번, 나머지는 프로필 순서대로 빈칸 없이 잇는다
// 지갑 속 물건(지폐, 지갑 속 쪽지, 지갑이 있을 때의 카드)은 칸이 없다
public static class ItemKeys
{
    static readonly List<ItemId> slots = new();

    public static List<ItemId> Slots()
    {
        slots.Clear();
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (profile == null) return slots;
        if (Note.Available) slots.Add(ItemId.Memo);
        if (profile.items == null) return slots;
        foreach (var id in profile.items)
        {
            if (id == ItemId.Memo || id == ItemId.Cash || (id == ItemId.Card && profile.Has(ItemId.Wallet))) continue;
            slots.Add(id);
        }
        if (HandRig.I != null && HandRig.I.HasReceipt) slots.Add(ItemId.Receipt);   // 얻으면 줄 끝에 붙는다
        return slots;
    }

    /// <summary>이 소지품의 번호. 칸이 없으면 0.</summary>
    public static int Of(ItemId id) => Slots().IndexOf(id) + 1;

    public static bool Pressed(Keyboard kb, ItemId id)
    {
        int n = Of(id);
        return n > 0 && kb[Key.Digit1 + (n - 1)].wasPressedThisFrame;
    }
}
