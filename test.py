from verse import verse

codes = ["ASW", "ASCB", "ASWDC", "NA-TWI", "TW", "TWI"]
passage = "John 3:16"

for code in codes:
    result = verse(passage, code)
    text = result.get("verses", [])
    if text:
        print(f"✅ {code}: {text[0][:60]}...")
    else:
        print(f"❌ {code}: No data")
