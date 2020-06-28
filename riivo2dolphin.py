import argparse
import struct
import xml.etree.ElementTree as ET
import os


def has_attribute(element, attribute):
    return attribute in element.attrib


def get_attribute(element, attribute, default=None):
    if attribute in element.attrib:
        return element.attrib[attribute]
    return default


BYTE_PATCH_FORMAT = "0x{:08X}:byte:0x{:08X}\n"
WORD_PATCH_FORMAT = "0x{:08X}:word:0x{:08X}\n"
DWORD_PATCH_FORMAT = "0x{:08X}:dword:0x{:08X}\n"


def parse_memory_patch(elem_memory, patch_lines: list, patch_path: str, patch_target: str):
    if has_attribute(elem_memory, "valuefile"):
        valuefile_path = '/'.join((patch_path, get_attribute(elem_memory, "valuefile").replace("{$__region}", patch_target)))
        data = open(valuefile_path, "rb").read()
    elif has_attribute(elem_memory, "value"):
        value_attrib = get_attribute(elem_memory, "value")
        data = bytes.fromhex(value_attrib)
    else:
        raise Exception("Err... there is no value or file to replace memory with...")

    offset = int(get_attribute(elem_memory, "offset", "0xFFFFFFFF"), 0)
    target = get_attribute(elem_memory, "target", "All")

    if target == "All" or target == patch_target:
        sub_offset = 0

        while sub_offset < len(data):
            remaining = len(data) - sub_offset

            # byte patch
            if remaining < 2:
                patch_lines.append(BYTE_PATCH_FORMAT.format(offset + sub_offset, data[sub_offset] & 0xFF))
                sub_offset += 1
            # word patch
            elif remaining < 4:
                patch_lines.append(WORD_PATCH_FORMAT.format(offset + sub_offset, struct.unpack_from(">H", data, sub_offset)[0]))
                sub_offset += 2
            # dword patch
            else:
                patch_lines.append(DWORD_PATCH_FORMAT.format(offset + sub_offset, struct.unpack_from(">I", data, sub_offset)[0]))
                sub_offset += 4


def parse_patch(elem_patch, patch_path: str, target: str):
    patch_lines = list()

    for elem_memory in elem_patch.findall("memory"):
        parse_memory_patch(elem_memory, patch_lines, patch_path, target)

    patch_lines.sort()
    return patch_lines


def riivo2dolphin(xml_file: str, folder: str = os.getcwd(), enabled_patches: list = list()):
    root = ET.parse('/'.join((folder, "riivolution", xml_file))).getroot()

    if not root.tag == "wiidisc":
        raise Exception("This file does not contain valid Riivolution information.")

    # Find game ID and target regions
    target_ids = list()
    elem_id = root.find("id")

    if elem_id:
        id_name = elem_id.attrib["game"]

        for elem_region in elem_id.findall("region"):
            target_ids.append(elem_region.attrib["type"])
    else:
        id_name = xml_file.replace(".xml", "")

    if len(target_ids) == 0:
        target_ids.append("All")

    # Find patches
    target_data = dict()

    for elem_patch in root.findall("patch"):
        patch_id = elem_patch.attrib["id"]
        patch_path = folder

        if "root" in elem_patch.attrib:
            patch_path += elem_patch.attrib["root"]  # root always starts with '/'

        for target in target_ids:
            if not target in target_data:
                target_data[target] = dict()

            target_data[target][patch_id] = parse_patch(elem_patch, patch_path, target)

    # Write target files
    for target, patches in target_data.items():
        patch_id_lines = list()

        with open(id_name + target + ".ini", "w") as f:
            f.write("[OnFrame]\n")
            for patch_id, patch_lines in patches.items():
                patch_id_line = "$" + patch_id + "\n"
                patch_id_lines.append(patch_id_line)

                f.write(patch_id_line)
                f.writelines(patch_lines)

            f.write("[OnFrame_Enabled]\n")
            if len(enabled_patches) == 0:
                f.writelines(patch_id_lines)
            else:
                for enabled_patch in enabled_patches:
                    f.write("$" + enabled_patch + "\n")

            f.flush()


parser = argparse.ArgumentParser(description="riivo2dolphin")
parser.add_argument("sd_root", type=str)
parser.add_argument("xml_file", type=str)
parser.add_argument("enabled_patches", nargs="*")
args = parser.parse_args()

if args.xml_file and args.sd_root:
    enabled_patches = args.enabled_patches if args.enabled_patches else list()
    riivo2dolphin(args.xml_file, args.sd_root, enabled_patches)
