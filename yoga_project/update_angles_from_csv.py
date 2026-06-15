import pickle
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


XLSX_PATH = Path(r"e:\nalla\videos\poses result\Ground_truth_angles_used_in_program.xlsx")
PKL_PATH = Path(r"e:\nalla\yoga_project\angles_final.pkl")

POSE_ALIASES = {
    "Warrior Ii": "Warrior II",
}


def _column_index(cell_ref):
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(f"Invalid Excel cell reference: {cell_ref}")

    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def _read_xlsx_rows(xlsx_path):
    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    with zipfile.ZipFile(xlsx_path) as workbook:
        shared_strings = []
        shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        for item in shared_root.findall("a:si", namespace):
            shared_strings.append("".join(text.text or "" for text in item.findall(".//a:t", namespace)))

        sheet_root = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []

        for row in sheet_root.findall(".//a:sheetData/a:row", namespace):
            values = []
            for cell in row.findall("a:c", namespace):
                cell_index = _column_index(cell.attrib["r"])
                while len(values) <= cell_index:
                    values.append("")

                raw_value = cell.find("a:v", namespace)
                if raw_value is None:
                    value = ""
                elif cell.attrib.get("t") == "s":
                    value = shared_strings[int(raw_value.text)]
                else:
                    value = raw_value.text

                values[cell_index] = value
            rows.append(values)

    width = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (width - len(row)))

    return rows


def load_xlsx_angles(xlsx_path):
    rows = _read_xlsx_rows(xlsx_path)
    if not rows or rows[0][0] != "Angle":
        raise ValueError("Expected first column header to be 'Angle'")

    headers = rows[0]
    angles_by_pose = {}

    for pose_name in headers[1:]:
        if pose_name:
            angles_by_pose[POSE_ALIASES.get(pose_name, pose_name)] = {}

    for row in rows[1:]:
        angle_name = row[0]
        if not angle_name:
            continue

        for pose_name, value in zip(headers[1:], row[1:]):
            if not pose_name or value in ("", None):
                continue

            target_pose = POSE_ALIASES.get(pose_name, pose_name)
            angles_by_pose[target_pose][angle_name] = float(value)

    return angles_by_pose


def backup_path_for(pkl_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return pkl_path.with_name(f"{pkl_path.stem}.backup_{timestamp}{pkl_path.suffix}")


def main():
    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"XLSX not found: {XLSX_PATH}")

    if not PKL_PATH.exists():
        raise FileNotFoundError(f"PKL not found: {PKL_PATH}")

    with open(PKL_PATH, "rb") as pkl_file:
        data = pickle.load(pkl_file)

    if not isinstance(data, dict):
        raise ValueError(f"Expected pickle data to be dict, got {type(data)}")

    new_angles = load_xlsx_angles(XLSX_PATH)
    backup_path = backup_path_for(PKL_PATH)

    with open(backup_path, "wb") as backup_file:
        pickle.dump(data, backup_file)

    if "angles" in data:
        data["angles"] = new_angles
    else:
        data = {"angles": new_angles}

    with open(PKL_PATH, "wb") as pkl_file:
        pickle.dump(data, pkl_file)

    print(f"Updated: {PKL_PATH}")
    print(f"Backup:  {backup_path}")
    print(f"Poses updated: {len(new_angles)}")
    for pose_name, pose_angles in new_angles.items():
        print(f"- {pose_name}: {len(pose_angles)} angles")


if __name__ == "__main__":
    main()
