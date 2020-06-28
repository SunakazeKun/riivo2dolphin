# riivo2dolphin
**riivo2dolphin** is a simple python script that creates INI files for Dolphin from Riivolution XML files. It converts any memory patch from the input file and writes them to separate INI files for each specified target region. In order to use this script you need to have Python 3 installed on your computer system.

# Usage
This is an easy-to-use script that is run from the command prompt:

    python riivo2dolphin.py [-h] sd_root xml_file [enabled_patches...]
*sd_root* is the path to the folder containing the *riivolution* directory and the mod's data.
*xml_file* is the XML file inside the *riivolution* folder that contains the patches.
*enabled_patches* is an array of patches that are enabled by default. If not specified, all patches are enabled!

Furthermore, memory patches can use the custom *target* attribute to restrict a memory patch to specific target regions only. Just edit the respective elements like this:

    <memory offset="0x806F0894" value="80001E70" original="8045A918" target="E"/>
This specific memory patch would only be included in the INI file for the target region *E*.
