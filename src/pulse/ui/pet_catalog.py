"""Code-rendered pets inspired by the two supplied reference sheets."""


def pet(id, name, species, coat, *, expression="idle", marking="#fff3e5"):
    return dict(id=id, name=name, species=species, coat=coat,
                expression=expression, marking=marking)


PETS = [
    pet("lavender", "Lavender", "round", "#c4a8fa"),
    pet("panda", "Panda", "panda", "#fffaff", marking="#393844"),
    pet("shiba", "Shiba", "cat", "#f5b66c", expression="happy"),
    pet("bunny", "Bunny", "bunny", "#fff1f8"),
    pet("bear", "Bear", "bear", "#c99075"),
    pet("calico", "Calico", "calico", "#fff0db", marking="#bf8a78"),
    pet("pig", "Pig", "pig", "#f9b4d5"),
    pet("chick", "Chick", "chick", "#ffe181", expression="happy"),
    pet("lavender-cat", "Lavender cat", "cat", "#bca0f5", expression="happy"),
    pet("penguin", "Penguin", "penguin", "#6899e9", expression="happy"),
    pet("frog", "Frog", "frog", "#9de1ad", expression="happy"),
    pet("koala", "Koala", "koala", "#b2a4e7"),
    pet("hamster", "Hamster", "hamster", "#f5b27e"),
    pet("capybara", "Capybara", "capybara", "#dfa17e", expression="sleepy"),
    pet("seal", "Seal", "seal", "#f9f8ff", expression="happy"),
    pet("blue-cat", "Blue cat", "cat", "#94cfff", expression="happy"),
    pet("puppy", "Puppy", "dog", "#fff0d7", marking="#bd8a72"),
    pet("fox", "Fox", "fox", "#ff9485", marking="#fff0dd"),
    pet("axolotl", "Axolotl", "axolotl", "#ffbad9", expression="happy"),
    pet("cow", "Lavender cow", "cow", "#d5baf8", marking="#a68add"),
    pet("charcoal-joy", "Charcoal joy", "round", "#41434e", expression="happy"),
    pet("lavender-calm", "Lavender calm", "round", "#c7adff"),
    pet("blue-joy", "Blue joy", "round", "#92caff", expression="happy"),
    pet("mint-wink", "Mint wink", "round", "#a0e9cf", expression="wink"),
    pet("peach-laugh", "Peach laugh", "round", "#ffd0a2", expression="laugh"),
    pet("pink-sleep", "Pink sleep", "round", "#ffb7db", expression="sleepy"),
    pet("yellow-rest", "Yellow rest", "round", "#ffe08c", expression="rest"),
    pet("teal-sparkle", "Teal sparkle", "round", "#52c4ca", expression="sparkle"),
    pet("blue-blush", "Blue blush", "round", "#93c7ff", expression="blush"),
    pet("mint-surprise", "Mint surprise", "round", "#a6ebd3", expression="surprised"),
    pet("rose-tears", "Rose tears", "round", "#fa93a5", expression="tears"),
    pet("peach-smug", "Peach smug", "round", "#ffc3a5", expression="smug"),
    pet("charcoal-grumpy", "Charcoal grumpy", "round", "#41434e", expression="grumpy"),
    pet("blue-playful", "Blue playful", "round", "#91c9ff", expression="playful"),
    pet("mint-kiss", "Mint kiss", "round", "#94e4d2", expression="kiss"),
    pet("yellow-smile", "Yellow smile", "round", "#ffe087"),
    pet("pink-yawn", "Pink yawn", "round", "#ffb8dc", expression="yawn"),
    pet("lavender-cheer", "Lavender cheer", "round", "#c4a8fc", expression="happy"),
]
BY_ID = {item["id"]: item for item in PETS}
