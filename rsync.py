import argparse
import os
import difflib


def get_argument():
    """Get arguments from standard input
    parser: parse argument
    return: command parser when calling argument"""
    parser = argparse.ArgumentParser()
    parser.add_argument('file_src', help='file source')
    parser.add_argument('file_dst', help='file destination')
    parser.add_argument('-u', '--update', action='store_true',
                        help='skip files that are newer on the receiver')
    parser.add_argument('-c', '--checksum', action='store_true',
                        help='skip based on checksum, not mod-time & size')
    return parser.parse_args()


def copy_symlink(file_src, file_dst, new_file):
    """Copy symlink from file source to file destination or directory
    check if file destination is a file or a directory,
    unlink if there is a file already exists"""
    if os.path.isfile(file_dst):
        if os.path.exists(file_dst):
            os.unlink(file_dst)
        os.symlink(file_src, file_dst)
    elif os.path.isdir(file_dst):
        if os.path.exists(new_file):
            os.unlink(new_file)
        os.symlink(file_src, new_file)
    else:
        os.symlink(file_src, file_dst)


def copy_hardlink(file_src, file_dst, new_file):
    """Copy hardlink from file source to file destination or directory
    check if file destination is a file or a directory,
    unlink if there is a file already exists"""
    if os.path.isfile(file_dst):
        if os.path.exists(file_dst):
            os.unlink(file_dst)
        os.link(file_src, file_dst)
    elif os.path.isdir(file_dst):
        if os.path.exists(new_file):
            os.unlink(new_file)
        os.link(file_src, new_file)
    else:
        os.link(file_src, file_dst)


def get_diff_position(file_src, file_dst):
    """Get different position in each file between
    file source and file destination
    generate an error if file source doesn't have the read right
    diff_position: different positio    n in each file
    compare_diff: a list of compared characters between two files
    content_src: content of file source
    content_dst: content of file destination
    d: shorten comand of difflib.Differ()
    return: diff_position"""
    diff_position = -1
    compare_diff = []
    try:
        with open(file_src, "r") as src, open(file_dst, "r") as dst:
            content_src = src.read()
            content_dst = dst.read()
            d = difflib.Differ()
            compare_diff = list(d.compare(content_src, content_dst))
    except PermissionError:
        print("rsync: send_files failed to open \"%s\": "
              "Permission denied (13)" % os.path.realpath(file_src))
    for i in range(len(compare_diff)):
        if compare_diff[i][0] == "-":
            diff_position = i
            break
    return diff_position


def copy_file(file_src, file_dst, st_src):
    """Copy file with below default behaviors:
    - Copy a file from source to destination, both files are strictly identical
    - The destination file will have the same permissions as the source file
    - The destination file will have the same access/modification times as
    the source file
    - Only copy the parts that are different between the source file and
    the destination file(if they are already identical, nothing is written!)
    diff_position: different position in each file
    """
    diff_position = get_diff_position(file_src, file_dst)
    if diff_position >= 0:
        with open(file_src, "r") as src, open(file_dst, "w") as dst:
            if diff_position >= 0:
                src.seek(diff_position)
                dst.seek(diff_position)
                diff_src = src.read()
                dst.write(diff_src)
    os.chmod(file_dst, st_src.st_mode)
    os.utime(file_dst, (st_src.st_atime, st_src.st_mtime))


def copy_file_default(file_src, file_dst):
    """Copy file with all default behavior:
    - Default behaviors of function copy_file()
    - Symlinks and hardlinks
    generate an error if file source doesn't exist
    new_file: new destination file if there is no existing destination file"""
    if not os.path.exists(file_src):
        print("rsync: link_stat \"%s\" failed: No such file or directory (2)"
              % os.path.realpath(file_src))
    else:
        new_file = file_dst + "/" + file_src
        st_src = os.stat(file_src)
        if os.path.islink(file_src):
            copy_symlink(file_src, file_dst, new_file)
        elif st_src.st_nlink >= 2:
            copy_hardlink(file_src, file_dst, new_file)
        elif os.path.isfile(file_dst):
            copy_file(file_src, file_dst, st_src)
        elif os.path.isdir(file_dst):
            if os.path.exists(new_file):
                copy_file(file_src, new_file, st_src)
            elif not os.path.exists(new_file):
                open(new_file, 'a').close()
                copy_file(file_src, new_file, st_src)
        else:
            open(file_dst, 'a').close()
            copy_file(file_src, file_dst, st_src)


def main():
    """Main function"""
    # Get command parser
    args = get_argument()
    # Get name and link of file source
    file_src = args.file_src
    # Get name and link of file destination
    file_dst = args.file_dst
    # Copy file with default behaviors
    copy_file_default(file_src, file_dst)


if __name__ == '__main__':
    main()
