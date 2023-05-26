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

# labels of issues to be plotted
labels = ["bug-high-prio", "bug-medium-prio", "bug-low-prio"]
# colors in reversed order
colors = ["#00ac46", "#fd8c00", "#780000"]

if __name__ == "__main__":
    # state all -> get all open and closed issues
    response = requests.get(url, params={"state": "all", "sort": "created"})
    issues = response.json()
    # Separate issues by open/closed status and label
    open_issues = {label: [] for label in labels}
    closed_issues = {label: [] for label in labels}

    for issue in issues:
        # get first label of issue that is in the list of labels
        issue_labels = [label["name"] for label in issue["labels"]]
        issue_label = None
        for label in labels:
            if label in issue_labels:
                issue_label = label
                break

        if issue_label:
            issue_info = {
                "created_at": datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                "closed_at": None if issue["closed_at"] is None else datetime.strptime(issue["closed_at"],
                                                                                       "%Y-%m-%dT%H:%M:%SZ"),
                "is_open": issue["closed_at"] is None,
                "label": [label["name"] for label in issue["labels"] if label["name"] in labels][0]
            }

            if issue_info["is_open"]:
                open_issues[issue_info["label"]].append(issue_info)
            else:
                closed_issues[issue_info["label"]].append(issue_info)

    merged_issues = {}
    dates = []

    for prio in open_issues:
        for issue in open_issues[prio]:
            if upper_date_limit.date() >= issue["created_at"].date():
                dates.append(issue["created_at"])
    for prio in closed_issues:
        for issue in open_issues[prio]:
            if upper_date_limit.date() >= issue["created_at"].date():
                dates.append(issue["created_at"])
    dates.sort()


    def get_amount_of_issues_on_day_from_label(current_date, label, list_of_issues):
        result = 0
        for i in list_of_issues[label]:
            if i["created_at"].date() <= current_date.date():
                result += 1
        return result


    def add_to_merged_issues(current_date, label_prefix, list_of_issues):
        for label in list_of_issues:
            amount = get_amount_of_issues_on_day_from_label(current_date, label, list_of_issues)
            label = label_prefix + label
            merged_issues[label].append(amount)


    for label in labels:
        merged_issues["closed-" + label] = []
    for label in labels:
        merged_issues["open-" + label] = []
    for date in dates:
        add_to_merged_issues(date, "open-", open_issues)
        add_to_merged_issues(date, "closed-", closed_issues)

    #    days = mdates.drange(now, then, dt.timedelta(days=1))

    fig, ax = plt.subplots()

    for date_id, date in enumerate(dates):
        for label_id, label in enumerate(labels):
            if label_id > 0:
                merged_issues["closed-" + label][date_id] += merged_issues["closed-" + labels[label_id - 1]][date_id]
                merged_issues["open-" + label][date_id] += merged_issues["open-" + labels[label_id - 1]][date_id]
            for inner_label in labels:
                merged_issues["open-" + label][date_id] += merged_issues["closed-" + inner_label][date_id]

    for label_id, label in enumerate(reversed(labels)):
        values = merged_issues["open-" + label]
        if values != [0] * len(values):
            ax.fill_between(
                dates, values, color="white"
            )
            ax.fill_between(
                dates, values, color=colors[label_id], alpha=0.15
            )
            ax.plot(dates, values, label="open-" + label, linewidth=2, color=colors[label_id])

    for label_id, label in enumerate(reversed(labels)):
        values = merged_issues["closed-" + label]
        if values != [0] * len(values):
            ax.fill_between(
                dates, values,
                label="closed-" + label, color=colors[label_id]
            )

    ax.legend(loc='upper left')
    ax.set_title('Bug Tracking')
    ax.set_xlabel('Datum')
    ax.set_ylabel('Anzahl an Bugs')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=2))

    plt.legend(loc='upper left')
    plt.tight_layout()

    plt.show()
