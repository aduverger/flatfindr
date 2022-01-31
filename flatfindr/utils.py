KEYWORDS = {
    "published": "Mis en vente il y a ",
    "price": "$ / mois",
    "address": "Montréal, QC",
    "surface(m2)": "mètres carrés",
    "surface(ft2)": "pieds carrés",
    "bedrooms": "chambres · ",
    "furnished": ("Meublé", "Non meublé"),
    "description": "Description",
    "day": "jours",
    "week": "semaine",
    "montreal": "Montréal, QC",
    "see_more": "Voir plus",
    "see_less": "Voir moins",
    "next_img": "Voir l’image suivante",
}


def make_url_clickable(val):
    # target _blank to open new window
    return f"<a target='_blank' href='{val}'>{val[-5:-1]}</a>"


def make_img_clickable(vals):
    # target _blank to open new window
    imgs = []
    cnt = 1
    for val in vals:
        imgs.append(f"<a target='_blank' href='{val}'>_{cnt}_</a>")
        cnt += 1
    return imgs


def make_address_clickable(val):
    #TODO Deal with `'` in the address
    href = (
        f"https://www.google.com/maps/place/{val.replace(' ', '+').replace('\'', '+')},+Montr%C3%A9al,+QC"
    )
    return f"<a target='_blank' href='{href}'>{val}</a>"
