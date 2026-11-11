"""Pluggable source adapters. Every adapter implements SourceAdapter.pull(); the mocks cycle through small pools of
synthetic multilingual items so the demo can inject fresh reports on demand. Real APIs replace a mock by implementing
the same interface (e.g. a regional social platform's API, an RSS news feed, the field app's sync endpoint)."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class FeedItem:
    text: str
    who: str              # source key, phone number or handle
    en: str | None = None  # verified translation, if the feed provides one


class SourceAdapter(Protocol):
    name: str
    channel: str
    description: str

    def pull(self, n: int = 1) -> list[FeedItem]: ...


class MockAdapter:
    def __init__(self, name: str, channel: str, description: str, items: list[FeedItem]):
        self.name, self.channel, self.description, self._items, self._i = name, channel, description, items, 0

    def pull(self, n: int = 1) -> list[FeedItem]:
        out = []
        for _ in range(n):
            out.append(self._items[self._i % len(self._items)])
            self._i += 1
        return out


ADAPTERS: dict[str, MockAdapter] = {a.name: a for a in [
    MockAdapter("citizen_sms", "sms", "Citizen SMS / voice in mixed languages", [
        FeedItem("ವಿರಾಜಪೇಟೆ ಮುಖ್ಯ ರಸ್ತೆಯಲ್ಲಿ ಮರ ಬಿದ್ದಿದೆ, ರಸ್ತೆ ಮುಚ್ಚಿದೆ", "+919812309001", "A tree has fallen on Virajpet main road, the road is closed"),
        FeedItem("napoklu alli 5 jana makkalu jothe sikkiddare, boat beku", "+919812309002", "5 people with children are stuck in Napoklu, a boat is needed"),
        FeedItem("सिद्दापुर में 15 लोगों को खाना चाहिए", "+919812309003", "15 people in Siddapura need food"),
    ]),
    MockAdapter("regional_social", "social_feed", "Regional-language social media (kn, ml, hi, ta, romanized)", [
        FeedItem("ಭಾಗಮಂಡಲದಲ್ಲಿ ನೀರಿನ ಮಟ್ಟ ಮತ್ತೆ ಏರುತ್ತಿದೆ, ಎಚ್ಚರಿಕೆ", "@bhagamandala_live", "The water level in Bhagamandala is rising again, be careful"),
        FeedItem("കുശാൽനഗറിൽ 30 പേർക്ക് ഭക്ഷണം വേണം", "@ml_kushal", "30 people in Kushalnagar need food"),
        FeedItem("विराजपेट में बिजली नहीं है, फोन चार्ज नहीं हो रहे", "@virajpet_hi", "There is no electricity in Virajpet, phones cannot be charged"),
        FeedItem("somwarpet road alli guddi kusidide, jagrathe", "@som_kanglish", "A hill has collapsed on the Somwarpet road, be careful"),
    ]),
    MockAdapter("news", "news_feed", "Regional news headlines (several languages)", [
        FeedItem("ಕೊಡಗು: ಪರಿಹಾರ ಶಿಬಿರಗಳಲ್ಲಿ 1,500 ಜನ", "news_kn", "Kodagu: 1,500 people in relief camps"),
        FeedItem("Kodagu: NDRF teams deployed to Napoklu and Bhagamandala", "news_en"),
        FeedItem("कोडगु: कावेरी का जलस्तर खतरे के निशान से ऊपर", "news_hi", "Kodagu: Cauvery water level above the danger mark"),
    ]),
    MockAdapter("field_team", "field_app", "Volunteer / field-team app reports", [
        FeedItem("SDRF Kodagu: Siddapura Govt School camp, 190 people, water ok for 2 days, need 40 blankets.", "sdrf"),
        FeedItem("ಮಡಿಕೇರಿ ಇಂದಿರಾನಗರದಲ್ಲಿ ಇನ್ನೂ 3 ಮನೆಗಳು ಅಪಾಯದಲ್ಲಿವೆ, 12 ಜನರನ್ನು ಸ್ಥಳಾಂತರಿಸಬೇಕು", "fire",
                 "3 more houses are at risk in Indira Nagar, Madikeri, 12 people must be evacuated"),
    ]),
    MockAdapter("official", "official_feed", "Official agency bulletins (English + Kannada)", [
        FeedItem("KSDMA: Bhagamandala–Napoklu road closed until further notice.", "ksdma"),
        FeedItem("ಕೊಡಗು ಜಿಲ್ಲಾಡಳಿತ: ಎಲ್ಲಾ ಪರಿಹಾರ ಶಿಬಿರಗಳು ತೆರೆದಿವೆ, ವದಂತಿಗಳನ್ನು ನಂಬಬೇಡಿ", "dc_office",
                 "Kodagu district administration: all relief camps are open, do not believe rumours"),
    ]),
    MockAdapter("missing_contact", "web", "Relatives / neighbours who cannot reach family (helpline, web, SMS)", [
        FeedItem("मेरे माता-पिता हट्टीहोले में हैं, कल से संपर्क नहीं हो रहा", "+919812309101", "My parents are in Hattihole, I have not been able to contact them since yesterday"),
        FeedItem("Neighbours from Hattihole not answering since last night, please send someone.", "+919812309102"),
    ]),
]}


def verified_translations() -> dict[str, str]:
    return {it.text: it.en for a in ADAPTERS.values() for it in a._items if it.en}
