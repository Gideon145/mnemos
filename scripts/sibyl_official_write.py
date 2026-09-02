"""One official-path memory write so usage shows in the server report."""
from sibyl_memory_client import MemoryClient


def main():
    memory = MemoryClient.local(r"C:\Users\vergio\.sibyl-memory\memory.db")
    memory.set_entity("preference", "build_cadence", {"value": "daily commits, tests before push"})
    record = memory.get_entity("preference", "build_cadence")
    print("wrote:", record is not None)
    memory.storage.close()


if __name__ == "__main__":
    main()
