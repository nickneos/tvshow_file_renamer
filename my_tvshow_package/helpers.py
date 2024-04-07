VIDEO_EXTS = [".avi", ".mp4", ".mkv"]


def is_video_file(file):
    """Checks if `file` is a video file"""
    for ext in VIDEO_EXTS:
        if file.lower().endswith(ext):
            return True
    return False


def all_equal(list):
    """Checks if all items in `list` are of the same value"""
    return all(x == list[0] for x in list)


def delist_if_needed(val):
    """If list has one value or all the same values, 'delist' it"""
    if type(val) is not list:
        return val
    elif len(val) == 0:
        return None
    elif all_equal(val):
        return val[0]
    else:
        return val
    

# test
assert delist_if_needed([1]) == 1
assert delist_if_needed(["a", "a", "a"]) == "a"
assert delist_if_needed(["a", "b", "c"]) == ["a", "b", "c"]
assert delist_if_needed("dog") == "dog"
assert delist_if_needed(None) == None
