## Motorola Boot Logo
---
Script to encode, decode Motorola boot logo binary file

### Requirements
- [Python 3](https://python.org)

### Usage
- Decoding/Extracting
```
$ moto-bootlogo.py -i logo.bin -o images
```

- Encoding/Compressing
```
$ moto-bootlogo.py -i images -o logo.bin
```

- List images, no decoding
```
$ moto-bootlogo.py -l logo.bin
```

### Reference
- [aboot](https://github.com/grub4android/lk/blob/master-uboot/app/aboot/aboot.c#L2710 "LK embedded kernel - aboot.c")
- [MotoBootLogoMaker](https://github.com/CaitSith2/MotoBootLogoMaker "CaitSith2 - MotoBootLogoMaker")
- [XDA Developers](https://forum.xda-developers.com/showpost.php?p=48859155&postcount=136 "Carock's XDA Post")