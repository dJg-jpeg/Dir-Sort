from threading import Thread
from pathlib import Path
import sys
import re
import shutil

FOLDERS_NAMES = ('image', 'video', 'audio', 'document', 'archive', 'unknown')
FILE_TYPES_EXTENSIONS = (
    ('.jpeg', '.jpg', '.png', '.svg'),
    ('.avi', '.mp4', '.mov', '.mkv'),
    ('.mp3', '.ogg', '.wav', '.amr'),
    ('.doc', '.docx', '.txt', '.pdf', '.xlsx', '.pptx'),
    ('.zip', '.gz', '.tar')
)


def get_cmd_args():
    if len(sys.argv) != 2:
        print("Insert only 1 argument")
    else:
        return sys.argv[1]


def check_file_extension(extension):
    for file_types in FILE_TYPES_EXTENSIONS:
        if extension in file_types:
            return FOLDERS_NAMES[FILE_TYPES_EXTENSIONS.index(file_types)]
    return FOLDERS_NAMES[5]


def find_all_files(path, files, finding_files_threads):
    for content in path:
        if content.is_file():
            extension = check_file_extension(get_filename_and_extension(content)[1])
            files[FOLDERS_NAMES.index(extension)].append(content)
        elif content.name not in FOLDERS_NAMES:
            finding_files_threads.append(
                Thread(
                    target=find_all_files, args=(content.iterdir(), files, finding_files_threads)
                )
            )
            finding_files_threads[-1].start()
            finding_files_threads[-1].join()
    return files


def make_dirs(path, sort_folders):
    for folder_name in FOLDERS_NAMES:
        if check_is_dir_exist(path / folder_name) is False:
            ((path / folder_name).mkdir())
        sort_folders.append(check_is_dir_exist(path / folder_name))


def check_is_dir_exist(path):
    if path.exists() is True:
        return path
    return path.exists()


def move_files(files, file_type_index, dirs):
    for file_path in files[file_type_index]:
        file_path.replace(dirs[file_type_index] / file_path.name)
        files[file_type_index][files[file_type_index].index(file_path)] = \
            dirs[file_type_index] / file_path.name


def unpack_archives(archives, archive_dir):
    for archive in archives:
        path_to_archive_dir = archive_dir / get_filename_and_extension(archive)[0]
        archive_path = path_to_archive_dir / archive.name
        path_to_archive_dir.mkdir()
        archive.replace(archive_path)
        archives[archives.index(archive)] = path_to_archive_dir
        shutil.unpack_archive(archive_path, path_to_archive_dir)
        archive_path.unlink()


def get_filename_and_extension(filename):
    return filename.resolve().stem, filename.suffix


def rename_files(files):
    for category in files:
        for content in category:
            filename = normalize(get_filename_and_extension(content)[0]) + get_filename_and_extension(content)[1]
            content.rename(content.parent / filename)
            files[files.index(category)][category.index(content)] = content.parent / filename


def remove_empty_dirs(path):
    for content in path:
        if content.is_dir() is True and len(list(content.iterdir())) > 0:
            remove_empty_dirs(content.iterdir())
        if content.is_dir() is True and len(list(content.iterdir())) == 0:
            content.rmdir()
        else:
            continue


def normalize(name):
    table_symbols = ('абвгґдеєжзиіїйклмнопрстуфхцчшщюяыэАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯЫЭьъЬЪ',
                     (
                         *u'abvhgde', 'ye', 'zh', *u'zyi', 'yi', *u'yklmnoprstuf', 'kh', 'ts',
                         'ch', 'sh', 'shch', 'yu', 'ya', 'y', 'ye', *u'ABVHGDE', 'Ye', 'Zh', *u'ZYI',
                         'Yi', *u'YKLMNOPRSTUF', 'KH', 'TS', 'CH', 'SH', 'SHCH', 'YU', 'YA', 'Y', 'YE',
                         *(u'_' * 4)
                     )
                     )
    map_cyr_to_latin = {ord(src): dest for src, dest in zip(*table_symbols)}
    rx = re.compile(r"[^\w_]")
    return rx.sub('_', name.translate(map_cyr_to_latin))


def main():
    p = Path(get_cmd_args())
    finding_files_threads = []
    moving_files_threads = []
    sort_folders = []
    if p.is_dir():
        all_files = list(find_all_files(p.iterdir(), [[], [], [], [], [], []], finding_files_threads))
        rename_files_thread = Thread(target=rename_files, args=(all_files,))
        make_new_dirs_thread = Thread(target=make_dirs, args=(p, sort_folders))
        rename_files_thread.start()
        make_new_dirs_thread.start()
        rename_files_thread.join()
        make_new_dirs_thread.join()
        for file_type_index in range(len(FOLDERS_NAMES)):
            moving_files_threads.append(
                Thread(target=move_files, args=(all_files, file_type_index, sort_folders))
            )
            moving_files_threads[-1].start()
        for this_thread in moving_files_threads:
            if this_thread.is_alive():
                this_thread.join()
        unpack_archives(all_files[4], sort_folders[4])
        remove_empty_dirs(p.iterdir())
        print("Sorted files : \n ", all_files)
    else:
        print('It is not a directory , please insert a valid directory path')


if __name__ == '__main__':
    main()
