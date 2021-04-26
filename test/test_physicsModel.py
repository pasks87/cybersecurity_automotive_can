import physicsModel
import matplotlib.pyplot as plt
# Test Temp
sm_temp = physicsModel.TempSubModel()
time = 0.0
cooling = True
v = 0
x_axe = []
y_axe = []

x_axe.append(time)
y_axe.append(363)
for i in range(900):
    if i == 10:
        cooling = False
    if i == 300:
        v = 50
    if i == 500:
        v = 100

    sm_temp.update(v, cooling, (time*1000))
    print("T engine: {}".format(sm_temp.T_engine))
    print("t start: {}".format(sm_temp.t_start/1000))
    time += 1
    x_axe.append(time)
    y_axe.append(sm_temp.T_engine)

plt.plot(x_axe, y_axe)
plt.show()

# # Test thermostat
# sm_thermostat = physicsModel.ThermostatSubModel()
# sm_thermostat.update(83)
# print("x_percent:{}".format(sm_thermostat.x_percent))
# print("T_percent:{}".format(sm_thermostat.T_percent))
# print("fi_rad:{}".format(sm_thermostat.fi_rad))
# print("fi_bypass:{}".format(sm_thermostat.fi_bypass))
#
# x_axe = []
# y_axe = []
# for elem in range(82, 98, 1):
#     x_axe.append(elem)
#     sm_thermostat.update(float(elem))
#     y_axe.append(sm_thermostat.x_percent)
# plt.plot(x_axe, y_axe)
# plt.show()

# #Test Aerodynamics sub model
# sm_aero = physicsModel.AerodynamicsSubModel()
# sm_aero.update(50, True)
# print(sm_aero.m_rad_fan)
# print(sm_aero.m_rad_v)
# print(sm_aero.m_rad)

# #Test Engine submodel
# sm_engine = physicsModel.EngineSubModel()
# sm_engine.update(145.0, 5, 50)
# print(sm_engine.P_t)
# print(sm_engine.N_engine)

# # Test look up table
# N_engine_labels = [1500.0, 2000.0, 25000.0, 3000.0, 3500.0, 4000.0]
# ch_labels = [0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5, 100.0]
# labels = [ch_labels, N_engine_labels]
# values = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#           [3.4, 4.6, 5.9, 6.8, 8.2, 9.5],
#           [7.2, 9.8, 11.5, 13.9, 16.7, 18.5],
#           [10.5, 14.1, 17.7, 20.8, 24.8, 28.2],
#           [14.0, 18.9, 23.6, 28.0, 33.1, 37.1],
#           [17.5, 23.9, 29.2, 35.2, 41.3, 50.9],
#           [21.5, 28.1, 35.1, 41.7, 49.5, 51.2],
#           [22.0, 33.4, 41.9, 46.7, 51.5, 51.2],
#           [22.0, 34.0, 43.2, 49.0, 51.5, 51.2]]
# P_t_lut = physicsModel.LookUpTable(labels, values)
#
# res = P_t_lut.get_value([50.1, 3000.1])
# print(res)
