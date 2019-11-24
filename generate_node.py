import random
import matplotlib.pyplot as plt
import math
import pickle

node_num = 7
x_list=[]
y_list=[]

plt.figure()
for i in range(node_num):
    x = 10 * random.random()
    y = 2 * random.random()
    # plt.annotate(str(i+1), xy=(x, y), xytext=(x+0.2, y+0.1),
    #              arrowprops=dict(facecolor='black', shrink=0.0005),
    #              )
    plt.text(x+0.05,y+0.05,str(i+1))
    x_list.append(x)
    y_list.append(y)
plt.plot(x_list,y_list,'.',color='red')
output = open('xlist.pkl', 'wb')
pickle.dump(x_list, output)
output.close()
output = open('ylist.pkl', 'wb')
pickle.dump(y_list, output)
output.close()

# mtable = [
#     [1, 1, 1, 0],
#     [1, 1, 1, 0],
#     [1, 1, 1, 1],
#     [0, 0, 1, 1],
# ]
mtable = [[0 for col in range(node_num)] for row in range(node_num)]
for i in range(0,node_num-1):
    for j in range(i+1, node_num):
        if math.sqrt(math.pow((x_list[i]-x_list[j]),2)+math.pow((y_list[i]-y_list[j]),2))<5:
            mtable[i][j] = 1
            plt.plot([x_list[i], x_list[j]],[y_list[i],y_list[j]],'-')
        else:
            mtable[i][j] = 0
        mtable[j][i] = mtable[i][j]

print(mtable)
output = open('data.pkl', 'wb')
pickle.dump(mtable, output)
output.close()
plt.show()


'''
        mtable=[
            [1, 1, 1, 0],
            [1, 1, 1, 0],
            [1, 1, 1, 1],
            [0, 0, 1, 1],
        ]
'''