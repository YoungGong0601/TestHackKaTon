// 키오스크 본체의 실물: 틈을 가린 종이, 틈으로 드나드는 카드, 영수증. 부착: PH_Kiosk_R4 루트
// 배치: cover = PosterFlap, slots = CardSlot 3개, card = Card(KioskCard), receipt = Receipt(KioskReceipt)
using UnityEngine;

public class KioskHardware : MonoBehaviour
{
    [SerializeField] PosterFlap cover;
    [SerializeField] CardSlot[] slots = new CardSlot[0];
    [SerializeField] KioskCard card;
    [SerializeField] KioskReceipt receipt;

    public bool CoverOpened => cover && cover.Opened;

    public void OpenCover() { if (cover) cover.Open(); }

    /// <summary>손님이 새로 설 때. 종이는 틈을 가리고 카드와 영수증은 없다.</summary>
    public void Clear()
    {
        if (cover) cover.Close();
        if (card) card.Hide();
        if (receipt) receipt.Clear();
    }

    public void CardAt(string id, Vector3 outward, KioskCard.Move move)
    {
        if (!card) return;
        foreach (var s in slots) if (s.id == id) { card.At(s.transform, outward, move); return; }
    }

    public void Print(string lines, string total, int number, float sec) { if (receipt) receipt.Print(lines, total, number, sec); }
    public void ReceiptReady() { if (receipt) receipt.CanTear(true); }
    public void Tear() { if (receipt) receipt.Tear(); }
}
