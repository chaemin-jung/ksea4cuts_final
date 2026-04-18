import subprocess

def print_image(filepath, copies=1):
    printer_name = "Canon_SELPHY_CP1500_2"

    for _ in range(copies):
        subprocess.run([
            "lpr",
            "-P", printer_name,
            "-o", "fit-to-page",
            "-o", "media=Postcard",
            filepath
        ], check=True)

    return True