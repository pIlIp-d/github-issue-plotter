# Copyright 2023 Philip Dell
# MIT-Licence

import requests
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

repo_owner = "OctoPi-Team"
repo_name = "OctoPi"
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

# only dates until this one are getting plotted
upper_date_limit = datetime(2023, 5, 27)

labels = []
colors = {}

# Separate issues by open/closed status and label
open_issues = {}
closed_issues = {}

# values for the graph
merged_issues = {}
dates = []


def get_issues():
    # state all -> get all open and closed issues
    response = requests.get(url, params={"state": "all", "sort": "created"})
    return response.json()


def get_datetime(string):
    return None if not string else datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    issues = get_issues()
    for issue in issues:
        # create mock for issues without Label
        if not issue["labels"]:
            issue["labels"] = [{"name": "No Label", "color": "aaaaaa"}]

        # get first label of issue that is in the list of labels
        issue_label = issue["labels"][0]["name"]

        # only if really an issue (not a pull request etc.)
        if issue_label and issue["node_id"].startswith("I_"):
            if issue_label not in labels:
                labels.append(issue_label)

            issue_info = {
                "created_at": get_datetime(issue["created_at"]),
                "closed_at": get_datetime(issue["closed_at"]),
                "is_open": issue["closed_at"] is None,
                "label": issue_label,
                "color": issue["labels"][0]["color"]
            }

            if not issue_info["is_open"]:
                if issue_info["label"] not in closed_issues.keys():
                    closed_issues[issue_info["label"]] = []
                closed_issues[issue_info["label"]].append(issue_info)

            if issue_info["label"] not in open_issues.keys():
                open_issues[issue_info["label"]] = []
            open_issues[issue_info["label"]].append(issue_info)
            colors[issue_info["label"]] = issue_info["color"]

    for prio in open_issues:
        for issue in open_issues[prio]:
            if upper_date_limit.date() >= issue["created_at"].date():
                dates.append(issue["created_at"])
    for prio in closed_issues:
        for issue in closed_issues[prio]:
            if upper_date_limit.date() >= issue["created_at"].date():
                dates.append(issue["created_at"])
            if upper_date_limit.date() >= issue["closed_at"].date():
                dates.append(issue["closed_at"])

    dates = sorted(dates)


    def get_amount_of_issues_on_day_from_label(current_date, label, list_of_issues, diff, key):
        result = 0
        for i in list_of_issues[label]:
            if i[key].date() <= current_date.date():
                result += diff
        return result


    def add_to_merged_issues(current_date, label_prefix, list_of_issues, key):
        for label in list_of_issues:
            amount = get_amount_of_issues_on_day_from_label(current_date, label, list_of_issues, 1, key)
            label = label_prefix + label
            merged_issues[label].append(amount)


    # init merged issues arrays
    for label in labels:
        merged_issues["closed-" + label] = []
    for label in labels:
        merged_issues["open-" + label] = []
    for date in dates:
        add_to_merged_issues(date, "open-", open_issues, "created_at")
        add_to_merged_issues(date, "closed-", closed_issues, "closed_at")

    fig, ax = plt.subplots()
    raw_merged_issues = merged_issues.copy()

    # cumulative sum the values
    for date_id, date in enumerate(dates):
        for label_id, label in enumerate(labels):
            if date_id >= len(merged_issues["closed-" + label]):
                merged_issues["closed-" + label].append(0)
            if date_id >= len(merged_issues["open-" + label]):
                merged_issues["open-" + label].append(0)
            if label_id > 0:
                merged_issues["closed-" + label][date_id] += merged_issues["closed-" + labels[label_id - 1]][date_id]
                merged_issues["open-" + label][date_id] += merged_issues["open-" + labels[label_id - 1]][date_id]

    # account for closed issues
    for date_id, date in enumerate(dates):
        for label_id, label in enumerate(labels):
            merged_issues["open-" + label][date_id] += merged_issues["closed-" + labels[-1]][date_id]
            merged_issues["open-" + label][date_id] -= merged_issues["closed-" + label][date_id]

    # plot open issues
    for label_id, label in enumerate(reversed(labels)):
        values = merged_issues["open-" + label]
        if values != [0] * len(values):
            ax.fill_between(dates, values, color="white")
            ax.fill_between(dates, values, color="#" + colors[label], alpha=0.15)
            ax.plot(dates, values, label="open-" + label, linewidth=2, color="#" + colors[label])

    # plot closed issues
    for label_id, label in enumerate(reversed(labels)):
        values = merged_issues["closed-" + label]
        if values != [0] * len(values):
            ax.fill_between(
                dates, values,
                label="closed-" + label, color="#" + colors[label]
            )

    ax.legend(loc='upper left')
    ax.set_title('Bug Tracking')
    ax.set_xlabel('Datum')
    ax.set_ylabel('Anzahl an Bugs')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=2))

    plt.legend(loc='upper left')
    plt.tight_layout()

    plt.savefig("diagram.png")
