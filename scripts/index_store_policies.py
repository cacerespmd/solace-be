
from app.ai.store_policies import index_store_policies


def main():
    result = index_store_policies()

    print("Store policy indexing completed.")
    print("Collection:", result["collection"])
    print("Policies indexed:", result["policies_indexed"])
    print("Official:", result["is_official"])


if __name__ == "__main__":
    main()
