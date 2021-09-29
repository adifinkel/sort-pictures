from pathlib import Path
from typing import List, Union
import json
import re

MAIN_DIR = 'E:\\pictures\\'
PICTURE_BY_DATE = 'pictures_by_date'
TO_BE_SORTED = 'to_be_sorted'
REGEX_FILE = 'reg.json'
BLACK_LIST_FILE = 'bl.json'
DUPLICATES_FILE = 'duplicates.json'
BLACK_REG_LIST = 'black_reg_list.json'
DIR_REG_LIST = 'directory_reg_list.json'


class PictureSort:
    START_YEAR = 1970
    END_YEAR = 2022

    def __init__(self, moving_path: Path):
        self.moving_path = moving_path
        with open(REGEX_FILE, 'r') as regex_fp,\
                open(BLACK_LIST_FILE, 'r') as black_list_fp,\
                open(DUPLICATES_FILE, 'r') as duplicates_fp, \
                open(DIR_REG_LIST, 'r') as dir_regex_fp, \
                open(BLACK_REG_LIST, 'r') as black_regex_fp:
            self._regexes = json.load(regex_fp)
            self._black_regexes = json.load(black_regex_fp)
            self._dir_regexes = json.load(dir_regex_fp)
            self._black_list = [Path(path) for path in json.load(black_list_fp)]
            self._duplicates = [Path(path) for path in json.load(duplicates_fp)]

    def add_to_regexes(self, regex: str):
        self._regexes.append(regex)
        # with open(REGEX_FILE, 'w') as regex_fp:
        #     json.dump(self._regexes, regex_fp, indent=4)

    def add_to_black_regexes(self, regex: str):
        self._black_regexes.append(regex)
        # with open(BLACK_REG_LIST, 'w') as black_regex_fp:
        #     json.dump(self._black_regexes, black_regex_fp, indent=4)

    def add_to_duplicates(self, path: Path):
        self._duplicates.append(path)
        with open(DUPLICATES_FILE, 'w') as duplicates_fp:
            json.dump([str(path) for path in self._duplicates], duplicates_fp, indent=4)

    def add_to_black_list(self, path: Path):
        self._black_list.append(path)
        # with open(BLACK_LIST_FILE, 'w') as black_list_fp:
        #     json.dump([str(path) for path in self._black_list], black_list_fp, indent=4)

    def add_to_dir_regexes(self, path: Path):
        self._dir_regexes.append(path)
        # with open(DIR_REG_LIST, 'w') as dir_regex_fp:
        #     json.dump([str(path) for path in self._dir_regexes], dir_regex_fp, indent=4)

    @staticmethod
    def get_content(dir_path: Path) -> (List[str], List[str]):
        """Return a list of files and a list of directories in path.

        Args:
            dir_path: the src directory path.

        Returns:
            A list of files and a list of directories in path.
        """
        files = []
        directories = []
        for c in dir_path.iterdir():
            if c.is_file():
                files.append(c)
            elif c.is_dir():
                directories.append(c)
            else:
                print(f'IDENTIFY ERROR: {c} is not a file or a dir')

        return files, directories

    @staticmethod
    def get_match_property(match, prop):
        try:
            return match.group(prop)
        except IndexError:
            return

    def get_destination_by_regex(self, file_path: Path, regex_list: List[str]) -> Union[Path, None]:
        """Return destination path if the file was parsed else return None. """
        for r in regex_list:
            match = re.search(f'^{r}$', file_path.stem)

            if match:
                year = self.get_match_property(match, 'year')
                month = self.get_match_property(match, 'month')
                day = self.get_match_property(match, 'day')

                if not (self.START_YEAR < int(year) < self.END_YEAR):
                    raise IndexError(f'Year {year} is not between {self.START_YEAR} and {self.END_YEAR} in file '
                                     f'{file_path}')
                dst = self.moving_path.joinpath(year)
                if month and day:
                    dst = dst.joinpath(f'{year}_{month}_{day}')

                return dst

        return

    def check_on_black_reg_list(self, file_path):
        for r in self._black_regexes:
            if re.match(f'^{r}$', file_path.stem):
                return True

        return False

    @staticmethod
    def should_get_regex_from_user():
        should_define_regex = None
        while should_define_regex is None:
            answer = input('Do you want to define a regex? [y, N] ')
            if answer in ('n', 'N', ''):
                return False
            elif answer in ('y', 'Y'):
                return True
            else:
                print('please press y/n')
        return

    @staticmethod
    def should_get_black_or_white_regex():
        should_get_black_or_white_regex = None
        while should_get_black_or_white_regex is None:
            answer = input('Do you want to define black or white regex? [b, W] ')
            if answer in ('w', 'W', ''):
                return 'white'
            elif answer in ('b', 'B'):
                return 'black'
            else:
                print('please press b/w')

    def handle_no_regex(self, file_path: Path, change_regex=True):
        if change_regex and self.should_get_regex_from_user():
            regex_type = self.should_get_black_or_white_regex()

            if regex_type == 'black':
                self.add_to_black_regexes(input('Insert black regex: '))
            else:
                self.add_to_regexes(input('Insert white regex: '))
        else:
            self.add_to_black_list(file_path)
        self.handle_file(file_path)

    def handle_file(self, file_path: Path, change_regex=True):
        if file_path in (self._black_list + self._duplicates):
            return

        if self.check_on_black_reg_list(file_path):
            return
        try:
            dst = self.get_destination_by_regex(file_path, self._regexes)
            if dst:
                dst.mkdir(parents=True, exist_ok=True)
                try:
                    file_path.rename(dst.joinpath(file_path.name))
                    print(f'Copied {file_path} to {dst}')
                except FileExistsError:
                    self.add_to_duplicates(file_path)
                    print(f'{file_path} is duplicated in {dst}')
            else:
                print(f'UNDEFINED REGEX ERROR: {file_path} has no Regex')
                self.handle_no_regex(file_path, change_regex)

        except IndexError as error:
            print(error)

            self.handle_no_regex(file_path)

    def handle_dir(self, dir_path: Path):
        dst = self.get_destination_by_regex(dir_path, regex_list=self._dir_regexes)
        if dst:
            dst.mkdir(parents=True, exist_ok=True)
            for f in dir_path.iterdir():
                try:
                    f.rename(dst.joinpath(f.name))
                    print(f'Copied {f} to {dst}')
                except FileExistsError:
                    self.add_to_duplicates(f)
                    print(f'{f} is duplicated in {dst}')
            return True
        return False

    def run(self, main_dir: Path, change_regex=True):
        directories = [main_dir]
        while directories:
            for directory in directories:
                handled = self.handle_dir(directory)
                if not handled:
                    inner_files, inner_dirs = self.get_content(directory)
                    directories.extend(inner_dirs)
                    for f in inner_files:
                        self.handle_file(f, change_regex)


if __name__ == '__main__':
    main_dir = Path(MAIN_DIR)
    PictureSort(main_dir.joinpath(PICTURE_BY_DATE)).run(main_dir.joinpath(TO_BE_SORTED), change_regex=False)
