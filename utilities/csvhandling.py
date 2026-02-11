import csv

# Title columns for this method are always "Category" and "Link", can be abstracted further later
def save_to_csv(file, results_to_save):
    with open(file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Link"])
        for category, link in results_to_save:
            writer.writerow([category, link])

def read_from_csv(file, operation = None, num = None):
    result = []
    with open(file, mode ='r')as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            if operation = "col"
                result.append(lines[num])
            else:
                return "NO OP GIVEN."
    return result