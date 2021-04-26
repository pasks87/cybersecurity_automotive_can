Code Reference carla_simulator
==================================================

File di configurazione *config.py*
--------------------------------------------------
.. automodule:: config

*Parametri di configurazione generali*

    .. autodata:: CARLA_path
        :annotation:

    .. autodata:: db_name
        :annotation:

*Parametri di configurazione per le ECU*

    .. autodata:: steer_idx

    .. autodata:: throttle_idx

    .. autodata:: brake_idx

    .. autodata:: reverse_idx

    .. autodata:: handbrake_idx

    .. autodata:: num_section_steer

    .. autodata:: num_section_pedals

    .. autodata:: num_section_speedometer

    .. autodata:: max_speed_spedometer



modulo *can_utilities.py*
--------------------------------------------------
.. automodule:: can_utilities

.. autofunction:: msg_to_string

.. autofunction:: decode_udp_msg

.. autoclass:: messageCodec
    :members:
    :undoc-members:

.. autoclass:: Sender
    :members:
    :undoc-members:

modulo *Carla_Classes.py*
--------------------------------------------------
.. module:: Carla_Classes

.. autofunction:: find_weather_presets

.. autofunction:: get_actor_display_name

.. autoclass:: World

.. autoclass:: DualControl
    :members:

    .. automethod:: _parse_vehicle_keys
    .. automethod:: _control_from_can_msg

.. autoclass:: HUD
    :members:

.. autoclass:: FadingText
    :members:

.. autoclass:: HelpText
    :members:

.. autoclass:: CollisionSensor
    :members:

.. autoclass:: LaneInvasionSensor
    :members:

.. autoclass:: GnssSensor
    :members:

.. autoclass:: CameraManager
    :members:

modulo *EcuClass.py*
--------------------------------------------------
.. module:: EcuClass

.. autoclass:: EcuClass
    :members:
    :no-undoc-members:

.. autoclass:: EcuClassSteer

.. autoclass:: EcuClassPedals

.. autoclass:: EcuClassVehicleInfo

modulo *dataExtractionClass.py*
--------------------------------------------------
.. module:: dataExtractionClass

.. autoclass:: DataExtractor
    :members:
