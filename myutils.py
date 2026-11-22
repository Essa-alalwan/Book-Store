import pandas as pd
import ollama

# AI model used for the assistant (must be installed in Ollama)
MODEL="qwen2.5:7b"

# columns every inventory table needs
COLUMNS=["Item Name","SKU","Price","Quantity","Category"]

# book categories used in the dropdowns and the table editor
CATEGORIES=["Fiction","Non-Fiction","Science","History","Kids","Comics","Other"]

# file where the inventory is auto-saved, so it survives a page refresh
DATA_FILE="saved_inventory.csv"


# create and return an empty inventory table
def empty_inventory():
    return pd.DataFrame(columns=COLUMNS)


# read a CSV and give back the table, but only if it has all the required columns
def load_inventory(file):
    df=pd.read_csv(file, dtype={"SKU": str})
    if not all(c in df.columns for c in COLUMNS):
        raise ValueError("Missing required columns")
    return df


# check if the entered SKU is already in the table
def sku_exists(df, sku):
    return sku in df["SKU"].astype(str).values


# add a new book to the bottom of the inventory table
def add_product(df, item, sku, price, quantity, category):
    new_row=pd.DataFrame({
        "Item Name":[item],
        "SKU":[sku],
        "Price":[price],
        "Quantity":[quantity],
        "Category":[category]
    })
    return pd.concat([df,new_row], ignore_index=True)


# change a book's quantity (restock adds, sale subtracts)
def update_stock(df, sku, action, amount):
    df=df.copy()
    df["SKU"]=df["SKU"].astype(str)
    mask=df["SKU"]==sku
    current=int(df.loc[mask,"Quantity"].iloc[0])
    if action=="Restock":
        df.loc[mask,"Quantity"]=current+amount
    else:
        if amount>current:
            raise ValueError(f"Not enough stock. Only {current} in stock.")
        df.loc[mask,"Quantity"]=current-amount
    return df


# return only the books that belong to one category
def filter_by_category(df, category):
    return df[df["Category"]==category]



# make sure Price and Quantity are numbers and not text
def with_numbers(df):
    df=df.copy()
    df["Price"]=pd.to_numeric(df["Price"])
    df["Quantity"]=pd.to_numeric(df["Quantity"])
    return df


# calculate the total money value of everything in stock
def total_value(df):
    df=with_numbers(df)
    return (df["Price"]*df["Quantity"]).sum()


# return the books whose quantity is below the threshold
def low_stock_items(df, threshold):
    df=with_numbers(df)
    return df[df["Quantity"]<threshold]


# send a prompt to the AI model and return its answer as text
def ask_ollama(prompt):
    response=ollama.chat(model=MODEL, messages=[{"role":"user","content":prompt}])
    return response["message"]["content"]


# build the text sent to the AI for a question 
def build_question_prompt(df, question):
    return (
        "You are a bookstore inventory assistant, when you answer include the books name and their quantity individually if applicable. Answer briefly using only this data.\n"
        f"Total inventory value: {total_value(df):.2f}\n"
        f"{df.to_csv(index=False)}\n"
        f"Question: {question}"
    )


# build the text sent to the AI for restock advice
def build_restock_prompt(low_df):
    low_df=low_df.copy()
    low_df["Quantity"]=low_df["Quantity"].astype(int)
    return (
        "You are a bookstore inventory assistant. These books are low on stock:\n"
        f"{low_df.to_csv(index=False)}\n"
        "Using only the data above, list which books to reorder first, ordered by lowest quantity. "
        "Give one short reason each, like 'only 3 copies left'. "
        "Do not add any outside information about the books."
    )


# load the auto-saved inventory, or start empty if the file is missing or broken
def load_saved_inventory():
    try:
        return load_inventory(DATA_FILE)
    except Exception:
        return empty_inventory()


# write the current inventory to the save file
def save_inventory(df):
    df.to_csv(DATA_FILE, index=False)