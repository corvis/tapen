from PIL import Image

from ptouch_py.core import get_first_printer
from ptouch_py.domain import TapeTextColor


def open_bitmap(file_path) -> Image.Image:
    return Image.open(file_path).convert("1", dither=3)


def main2():
    image = open_bitmap("/srv/projects/ptouch-py/test.png")
    printer = get_first_printer()
    if printer:
        print("Found printer: " + str(printer))
    else:
        print("Device is not detected")
        return
    printer.init()
    #status = printer.get_status()
    #print("Detected tape: {}mm {} on {}".format(status.tape_width, status.text_color, status.tape_color))
    # printer.print_image(image)
    print(TapeTextColor.get_by_code(4))

if __name__ == "__main__":
    main2()
