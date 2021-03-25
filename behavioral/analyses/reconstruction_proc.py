# must run in Python 2

from data_utilities import *
import matplotlib.pyplot as plt
import random
from itertools import cycle

raw_data = load_json('../reconstruction_data.json')
start_with_subject = 132
end_with_subject = 200

# get coordinates
data = {}
for sid in raw_data:
    if not sid.isdigit():
        continue
    data[sid] = list(raw_data[sid].values())[0]['data']
    # change keys from image names to hierarchy positions
    hierarchy = [str(i) for i in range(1, 10)]
    random.seed(int(sid))
    random.shuffle(hierarchy)
    img_names = list(data[sid].keys())
    for img in img_names:
        if 'undefined' in img:
            data[sid].pop(img)
            continue
        pos = hierarchy.index(img[1])
        data[sid][pos] = data[sid].pop(img)
    # dict -> list
    data[sid] = [data[sid][key] for key in sorted(data[sid])]

# plot
plt.figure(figsize=(100, 100))
counter = 0
for sid in sorted(data.keys()):
    if int(sid) < start_with_subject or int(sid) > end_with_subject:
        continue
    counter += 1
    zipped = list(zip(*data[sid]))
    # reverse y axis
    plt.subplot(4, 8, counter)
    plt.scatter(zipped[0], [-1 * z for z in zipped[1]], s=[i for i in range(1000, 1, -100)], alpha=0.2)
    plt.title(sid, position=(0.9, 0.1))
    plt.tick_params(which='both', bottom=False, top=False, left=False, right=False, labelsize=0)
    axes = plt.gca()
    axes.set_xlim([-60, 890])
    axes.set_ylim([-890, 60])
plt.tight_layout()
plt.show()
