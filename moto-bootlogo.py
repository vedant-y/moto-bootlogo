import argparse
import sys
import os
import io
import json
import hashlib
from PIL import Image

class MotoBootLogo:
    def __init__(self, input, output, list):
        if list:
            if os.path.isfile(list):
                self.decode(list, None); return
        elif os.path.isfile(input):
            self.decode(input, output); return
        elif os.path.isdir(input):
            self.encode(input, output); return
        print("[-] Input FILE/DIR inaccessible")

    def intFromByte(self, bytes=1):
        return int.from_bytes(self.infile.read(bytes), byteorder="little", signed=True)

    def uintFromByte(self, bytes=1):
        return int.from_bytes(self.infile.read(bytes), byteorder="little", signed=False)

    def strFromByte(self, bytes=1, encoding="ASCII"):
        return str(self.infile.read(bytes), encoding)

    def intToByte(self, integer, length=1):
        return (integer).to_bytes(length, byteorder="little", signed=True)

    def uintToByte(self, integer, length=1):
        return (integer).to_bytes(length, byteorder="little", signed=False)

    def strToByte(self, str, encoding="ASCII"):
        return str.encode(encoding)

    def decode(self, filename, dirname):
        print("[+] Input [%s] => Output [%s]" % (filename, dirname))
        
        self.infile = open(filename, "rb")
        
        # Motorola bootlogo container, "MotoLogo\x00" Header, 9 bytes
        if (self.intFromByte(8) != 0x6F676F4C6F746F4D or self.intFromByte() != 0x00):
            print("[-] Invalid binary file header")
            return

        data = {}
        data['count'] = int((self.intFromByte(4) - 0x0D) / 0x20)
        print("[+] %s Images found" % (data['count']))

        data['name'], offset, size = ([] for i in range(3))
        for i in range(data['count']):
            self.infile.seek(0x0D + (0x20 * i))
            data['name'].append(self.strFromByte(24).split("\0")[0])
            offset.append(self.intFromByte(4))
            size.append(self.intFromByte(4))

        data['version'] = self.intFromByte(4)
        if data['version'] == -1:
            pass
        elif data['version'] == -2:
            data['device'] = self.strFromByte(self.intFromByte(4))
            data['text'] = self.strFromByte(self.intFromByte(4), "ASCII")
            data['comment'] = self.strFromByte(self.intFromByte(4))
            data['resx'] = self.intFromByte(2)
            data['resy'] = self.intFromByte(2)

            print("[+] Device: %s" % (data['device']))
            print("[+] Comment: %s" % (data['text']))
            print("[+] Comment: %s" % (data['comment']))
            print("[+] Resolution: %sx%s" % (data['resx'], data['resy']))
        else:
            print("[-] Unsupported binary file version")
            return

        if dirname is None:
            print("[+] Binary file version: %s\n" % (data['version']))
            print("[+] Name, Offset, Size")
            for i in range(data['count']):
                print("[+] %s, %s, %s" % (data['name'][i], offset[i], size[i]))
            return

        # Motorola RLE bootlogo, "MotoRun\x00" Header, 8 bytes
        self.infile.seek(offset[0])
        if (self.intFromByte(8) != 0x006E75526F746F4D):
            print("[-] Invalid RLE image header")
            return

        os.makedirs(dirname, exist_ok=True)
        for i in range(data['count']):
            print("[+] Processing %s" % (data['name'][i]))
            
            self.infile.seek(offset[i] + 8)
            x = self.intFromByte() << 8
            x = x | self.uintFromByte()
            y = self.intFromByte() << 8
            y = y | self.uintFromByte()
            img = Image.new("RGB", (x, y))
            xx = yy = 0
            while (yy < y):
                pixelcount = self.intFromByte() << 8
                pixelcount = pixelcount | self.uintFromByte()
                repeat = (pixelcount & 0x8000) == 0x8000
                pixelcount = pixelcount & 0x7FFF
                red = green = blue = 0
                if (repeat):
                    blue = self.uintFromByte()
                    green = self.uintFromByte()
                    red = self.uintFromByte()
                    while (pixelcount > 0):
                        pixelcount = pixelcount - 1
                        img.putpixel((xx, yy), (red, green, blue))
                        xx = xx + 1
                        if (xx != x): continue
                        xx = 0
                        yy = yy + 1
                        if (yy == y): break
                else:
                    while (pixelcount > 0):
                        pixelcount = pixelcount - 1
                        blue = self.uintFromByte()
                        green = self.uintFromByte()
                        red = self.uintFromByte()
                        img.putpixel((xx, yy), (red, green, blue))
                        xx = xx + 1
                        if (xx != x): continue
                        xx = 0
                        yy = yy + 1
                        if (yy == y): break
            img.save("%s/%s.png" % (dirname, data['name'][i]), format="PNG")

        self.infile.close()
        with open(dirname + "/data.json", 'w') as dfile:
            json.dump(data, dfile, indent=2)

    def encode(self, dirname, filename):
        print("[+] Input [%s] => Output [%s]" % (dirname, filename))
        
        try:
            with open(dirname + "/data.json") as dfile:
                data = json.load(dfile)
        except Exception:
            print("[-] " + dirname + "/data.json inaccessible")
            return

        print("[+] %s Images found" % (data['count']))
        if data['count'] != len(data['name']):
            print("[-] Image list not equal to image count")
            return

        stream = io.BytesIO()

        # Motorola bootlogo container, "MotoLogo\x00" Header, 9 bytes
        stream.write(self.intToByte(0x6F676F4C6F746F4D, 9))

        stream.write(self.intToByte(0x0D + (data['count'] * 0x20), 4))
        for i in range(data['count']):
            stream.seek(0x0D + (i * 0x20))
            name = self.strToByte(data['name'][i])
            stream.write(name)
            stream.write(self.intToByte(0, 0x20 - len(name)))

        stream.write(self.intToByte(data['version'], 4))
        if data['version'] == -1:
            pass
        elif data['version'] == -2:
            print("[+] Device: %s" % (data['device']))
            print("[+] Comment: %s" % (data['text']))
            print("[+] Comment: %s" % (data['comment']))
            print("[+] Resolution: %sx%s" % (data['resx'], data['resy']))

            stream.write(self.intToByte(len(data['device']), 4))
            stream.write(self.strToByte(data['device']))
            stream.write(self.intToByte(len(data['text']), 4))
            stream.write(self.strToByte(data['text']))
            stream.write(self.intToByte(len(data['comment']), 4))
            stream.write(self.strToByte(data['comment']))
            stream.write(self.intToByte(data['resx'], 2))
            stream.write(self.intToByte(data['resy'], 2))
        else:
            print("[-] Unsupported binary file version, using common")
            data['version'] = -1

        hashes, offset, size = ([] for i in range(3))
        for i in range(data['count']):
            while ((stream.tell() % 0x200) != 0):
                stream.write(self.uintToByte(0xFF))

            print("[+] Processing %s" % (data['name'][i]))
            try:
                img = Image.open("%s/%s.png" % (dirname, data['name'][i]))
                result = self.encodeImg(img)
            except Exception:
                print("[-] Image corrupt or inaccessible")
                return

            tempoffset = stream.tell()
            tempsize = len(result)
            hash = hashlib.md5(result).hexdigest()

            if hash in hashes:
                index = hashes.index(hash)
                tempoffset = offset[index]
                tempsize = size[index]
            else:
                hashes.append(hash)
                offset.append(tempoffset)
                size.append(tempsize)
                stream.write(result)

            stream.seek(0x0D + 0x18 + (i * 0x20))
            stream.write(self.intToByte(tempoffset, 4))
            stream.write(self.intToByte(tempsize, 4))
            stream.seek(0, io.SEEK_END)

        with open(filename, "wb") as outfile:
            outfile.write(stream.getvalue())

    def encodeImg(self, img):
        data = io.BytesIO()

        # Motorola RLE bootlogo, "MotoRun\x00" Header, 8 bytes
        data.write(self.intToByte(0x006E75526F746F4D, 8))

        data.write(self.intToByte(img.width >> 8))
        data.write(self.uintToByte(img.width & 0xFF))
        data.write(self.intToByte(img.height >> 8))
        data.write(self.uintToByte(img.height & 0xFF))
        
        for y in range(0, img.height):
            colors = []
            for x in range(0, img.width):
                colors.append(img.getpixel((x, y)))
            row = self.encodeRow(colors)
            data.write(row)
        return data.getvalue()

    def encodeRow(self, colors):
        data = io.BytesIO()
        i = 0
        count = len(colors)
        while (i < count):
            j = i
            while ((j < count) and (colors[i] == colors[j])): j = j + 1
            if ((j - i) > 1):
                data.write(self.uintToByte((0x80 | ((j - i) >> 8))))
                data.write(self.uintToByte(((j - i) & 0xFF)))
                data.write(self.uintToByte(colors[i][2]))
                data.write(self.uintToByte(colors[i][1]))
                data.write(self.uintToByte(colors[i][0]))
                i = j
            else:
                k = j
                while True:
                    j = k - 1
                    while ((k < count) and (colors[j] != colors[k])): j = j + 1; k = k + 1
                    while ((k < count) and (colors[j] == colors[k])): k = k + 1
                    if (k == count): break
                    l = k
                    while ((l < count) and (colors[k] == colors[l])): l = l + 1
                    if not (((k - j) < 3) and ((l - k) < 2)): break
                if ((j - i) == 0):
                    data.write(self.intToByte(0))
                    data.write(self.intToByte(1))
                    data.write(self.uintToByte(colors[count - 1][2]))
                    data.write(self.uintToByte(colors[count - 1][1]))
                    data.write(self.uintToByte(colors[count - 1][0]))
                    break
                if (j == (count - 1)): j = j + 1
                data.write(self.uintToByte(((j - i) >> 8)))
                data.write(self.uintToByte(((j - i) & 0xFF)))
                k = 0
                while (k < (j - i)):
                    data.write(self.uintToByte(colors[i + k][2]))
                    data.write(self.uintToByte(colors[i + k][1]))
                    data.write(self.uintToByte(colors[i + k][0]))
                    k = k + 1
                i = j
        return data.getvalue()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    list = '-l' in sys.argv
    parser.add_argument('-i', required=not list, dest='INPUT', help='FILE/DIR')
    parser.add_argument('-o', required=not list, dest='OUTPUT', help='DIR/FILE')
    parser.add_argument('-l', required=list, dest='FILE', help='List images, no decoding')
    args = parser.parse_args()

    mbl = MotoBootLogo(args.INPUT, args.OUTPUT, args.FILE)
