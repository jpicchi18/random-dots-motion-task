import pandas as pd

pd.read_csv('data.csv') 

y=np.array([1,1,2,1,-2])
x=np.array([0,1,2,3,4])
integral_threshhold = -10
# create new column in dataframe that holds coords for integration
df["integral"] = -1
df["is_COM"] = 0
# enumerate over all participants
# for name in df.name.unique():
#   entries = df[df[‘name’] == name] # change later
x_dim, y_dim = df.shape
# get x_coord of start position (varies due to screen size)
start_position = 863
# loop over cursor position dicts
for i in range(x_dim):
  # find which side they selected (target 1 = left, target 2 = right)
  target_selected = 'left'
  if (int(df.iloc[i, 6]) == 2):
    target_selected = 'right'
    al(df.iloc[i, 5])
  x_coords = []
  y_coords = []
  # loop over cursor coordinates in the dictionary
  first = True
  for key in sorted(cursor_pos):
    if first:
      first = False
      start_position = cursor_pos[key][0]
      continue
    x_coord = cursor_pos[key][0] - start_position
    y_coord = cursor_pos[key][1]
    # set x_coord to 0 if it is on the side of the selected targets
    if (target_selected == 'left' and x_coord < 0) or (target_selected == 'right' and x_coord > 0):
      x_coord = 0
    # switch coords and append coords to list
    x_coords.append(y_coord)
    y_coords.append(np.abs(x_coord))
  # print(y_coords)
  # compute integral and store
  df.at[i, "integral"] = scipy.integrate.trapz(y_coords, x_coords)
  if (df.iloc[i, 18]) < integral_threshhold:
    df.at[i, "is_COM"] = 1













