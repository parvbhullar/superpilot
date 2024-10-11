from superpilot.core.configuration import SystemConfiguration, SystemSettings


class MemoryConfiguration(SystemConfiguration):
    pass


class MemorySettings(SystemSettings):
    configuration: MemoryConfiguration
