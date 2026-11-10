from django.utils.text import slugify

_TRANSLIT = {
    'а': 'a', 'ә': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ғ': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'і': 'i', 'й': 'y', 'к': 'k', 'қ': 'q', 'л': 'l', 'м': 'm',
    'н': 'n', 'ң': 'n', 'о': 'o', 'ө': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ұ': 'u', 'ү': 'u', 'ф': 'f', 'х': 'kh', 'һ': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh',
    'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def transliterate(text):
    """Қазақ/орыс әріптерін латынға айналдырады (URL slug үшін)."""
    return ''.join(_TRANSLIT.get(ch, ch) for ch in text.lower())


def unique_slug(model, title, max_length=200, exclude_pk=None):
    """Тақырыптан бірегей ASCII slug жасайды: «Қазақстан туры» -> qazaqstan-tury."""
    base = slugify(transliterate(title))[:max_length - 6].strip('-') or 'tour'
    slug, counter = base, 1
    qs = model.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug
