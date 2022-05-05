import nuke


def shogtun_write_update(version="1.0"):

    if version == "1.0":
        print("Start Hotfix : shogtun_write_update - version : {0}".format(version))
        profile_mapping = [
            ["Mono Exr, 32 bit - Zip 1", "Comp - Mono Exr, 32 bit - Zip 1"],
            ["Mono Exr, 16 bit - Zip 1", "Comp - Mono Exr, 16 bit - Zip 1"],
            ["Mono Dpx", "Matte - Mono Dpx"],
            ["Mono Tga", "X - Mono Dpx"],
            ["Mono Png", "Comp - Mono Exr, 32 bit - Zip 1"],
            ["Mono Exr, 32 bit - Zip 1", "Comp - Mono Exr, 32 bit - Zip 1"],
            ["Mono Exr, 32 bit - Zip 1", "Comp - Mono Exr, 32 bit - Zip 1"],
            ["Mono Exr, 32 bit - Zip 1", "Comp - Mono Exr, 32 bit - Zip 1"],
        ]
        node_type = "WriteTank"
        not_found = "[Not Found]"
        for node in nuke.allNodes(node_type):
            print("\t - Node : {0}".format(node.name()))
            profile_orig = node.knob("tk_profile_list").value()
            if not_found in profile_orig:
                # looking for a new profile
                new_profile = None
                for item in profile_mapping:
                    if "{0} {1}".format(item[0], not_found) == profile_orig:
                        new_profile = item[1]
                        break
                if new_profile:
                    print("\t\t update profile : {0} > {1}".format(profile_orig, new_profile))
                    node.knob("tk_profile_list").setValue(new_profile)
