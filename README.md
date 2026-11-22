# Bookstore Inventory Manager

A simple web app that helps a bookstore track its books, stock and total value, instead of using notebooks. Built with Python, Streamlit and pandas.

**Video demo:** [Watch the demo](https://drive.google.com/file/d/1iXZ8wiVd-p8HyqzDLyLRNgBY9xqbqVEo/view?usp=sharing)

**Live app:** [Open the app](https://book-store-isa.streamlit.app/)

## What it does

- **Add Product:** add a book (name, SKU, price, quantity, category). Empty fields and duplicate SKUs are blocked.
- **Update Stock:** restock or sell copies of a book. You can't sell more than you have.
- **Search/Filter:** show the books of one category.
- **Inventory View:** see all books, the total inventory value and a low stock warning (books below your chosen number turn red).
- **Edit Table:** edit the table directly like a spreadsheet.
- **AI Assistant:** ask questions about your stock and get restock advice. It runs locally with Ollama.
- **Upload / Download CSV:** load your inventory from a CSV and download it again. The app also auto-saves, so your books stay after a refresh.

## How to run

1. Install the packages:
   ```
   pip install -r requirements.txt
   ```
2. For the AI Assistant, install [Ollama](https://ollama.com) and download the model:
   ```
   ollama pull qwen2.5:7b
   ```
3. Start the app:
   ```
   python -m streamlit run app.py
   ```

## Files

- `app.py`: the Streamlit pages
- `myutils.py`: the logic functions
- `demo_inventory.csv`: sample data
- `requirements.txt`: Python packages

## CSV columns

`Item Name, SKU, Price, Quantity, Category`

