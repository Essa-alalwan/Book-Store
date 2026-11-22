import streamlit as st
import myutils

# load the saved books when the app starts, starts empty if there's no save file
if "inventory" not in st.session_state:
    st.session_state["inventory"]=myutils.load_saved_inventory()

# remember the last uploaded file so we don't load it twice
if "loaded_file" not in st.session_state:
    st.session_state["loaded_file"]=None

# sidebar menu to switch between the pages
with st.sidebar:
    page_chosen = st.radio(
        "MENU",
        ("Add Product", "Update Stock","Search/Filter","Inventory View","Edit Table","AI Assistant")
    )

    # upload a CSV, but only load it if it's new and has the right columns
    uploaded_file=st.file_uploader("Upload inventory CSV", type="csv")
    if uploaded_file is not None and uploaded_file.name != st.session_state["loaded_file"]:
        try:
            st.session_state["inventory"]=myutils.load_inventory(uploaded_file)
            st.session_state["loaded_file"]=uploaded_file.name
        except ValueError:
            st.error("The CSV must have these columns: Item Name, SKU, Price, Quantity, Category")
        except Exception:
            st.error("Could not read this file. Make sure it is a valid CSV with a header row.")

# Add Product page, fill in the form to add a new book
if page_chosen=="Add Product":
    st.title("Add Product")
    item=st.text_input("what is the book name")
    sku=st.text_input("SKU value")
    price=st.number_input("Price", min_value=0.0, step=0.5)
    quantity=st.number_input("quantity in stock", min_value=0, step=1)
    category=st.selectbox("Category", myutils.CATEGORIES)

    # when the button is clicked, check the values first and only then add the book
    if st.button("Add Product"):
        if item.strip()=="" or sku.strip()=="":
            st.warning("Book name and SKU can't be empty")
        elif price<=0:
            st.warning("Price must be greater than 0")
        elif quantity<=0:
            st.warning("Quantity must be greater than 0")
        elif myutils.sku_exists(st.session_state["inventory"], sku.strip()):
            st.error("This SKU already exists")
        else:
            st.session_state["inventory"]=myutils.add_product(
                st.session_state["inventory"], item.strip(), sku.strip(), price, quantity, category
            )
            st.write("Done")

# Update Stock page, pick a book, then restock or sell some copies
elif page_chosen=="Update Stock":
    st.title("Update Stock")
    df=st.session_state["inventory"]
    if len(df)==0:
        st.write("No products yet")
    else:
        # show the SKU with the book name so it's easy to recognize
        labels=df["SKU"].astype(str)+" - "+df["Item Name"]
        chosen=st.selectbox("Choose book", labels)
        selected_sku=chosen.split(" - ")[0]
        action=st.radio("Action", ("Restock","Sale"))
        amount=st.number_input("Amount", min_value=1, step=1)

        # only save the change if there's no error (like selling more than we have)
        if st.button("Update"):
            try:
                updated_df=myutils.update_stock(df, selected_sku, action, amount)
                st.session_state["inventory"]=updated_df
                st.write("Updated")
                updated_df
            except ValueError as error:
                st.error(str(error))

# Search/Filter page, pick a category and see only its books
elif page_chosen=="Search/Filter":
    st.title("Search/Filter")
    chosen_category=st.selectbox("Category", myutils.CATEGORIES)
    filtered_df=myutils.filter_by_category(st.session_state["inventory"], chosen_category)
    st.dataframe(filtered_df)

# Inventory View page, total value, low stock warning and the full table
elif page_chosen=="Inventory View":
    st.title("Inventory View")
    df=myutils.with_numbers(st.session_state["inventory"])

    st.metric("Total inventory value", f"{myutils.total_value(df):,.2f}")

    # the user decides what counts as low stock
    threshold=st.number_input("Low stock threshold", min_value=0, value=5, step=1)
    low_stock=myutils.low_stock_items(df, threshold)
    if len(low_stock)>0:
        st.warning(f"{len(low_stock)} item(s) below {threshold}")

    # colors a row red if its quantity is below the threshold
    def highlight_low(row):
        if row["Quantity"]<threshold:
            return ["background-color: #ff6b6b; color: black"]*len(row)
        return [""]*len(row)

    # show the table with red rows and cleaner number formatting
    st.dataframe(df.style.apply(highlight_low, axis=1).format({"Price":"{:.2f}","Quantity":"{:.0f}"}))

# Edit Table page, edit the table directly like a spreadsheet
elif page_chosen=="Edit Table":
    st.title("Edit Table")
    st.write("Click any cell to change it. Use the + row at the bottom to add a book, or select a row and press Delete to remove it.")
    edited_df=st.data_editor(
        st.session_state["inventory"],
        num_rows="dynamic",
        # rules for each column so bad values can't be typed in
        column_config={
            "Price": st.column_config.NumberColumn("Price", min_value=0.0),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
            "Category": st.column_config.SelectboxColumn("Category", options=myutils.CATEGORIES)
        }
    )
    # save the edits so every page sees them
    st.session_state["inventory"]=edited_df

# AI Assistant page, ask questions and get restock advice from the local AI
elif page_chosen=="AI Assistant":
    st.title("AI Assistant")
    df=st.session_state["inventory"]
    if len(df)==0:
        st.write("No products yet")
    else:
        st.subheader("Ask a question")
        question=st.text_input("Ask about your inventory")
        if st.button("Ask"):
            if question.strip()=="":
                st.warning("Type a question first")
            else:
                # try/except so the app doesn't crash if Ollama isn't running
                try:
                    with st.spinner("Thinking..."):
                        st.write(myutils.ask_ollama(myutils.build_question_prompt(df, question)))
                except Exception:
                    st.error("Could not reach Ollama. Make sure it is running and the model is installed.")

        st.subheader("Restock advice")
        ai_threshold=st.number_input("Low stock threshold for advice", min_value=0, value=5, step=1)
        if st.button("Get restock advice"):
            # only send the low stock books to the AI
            low=myutils.low_stock_items(df, ai_threshold)
            if len(low)==0:
                st.write("Nothing is low on stock.")
            else:
                try:
                    with st.spinner("Thinking..."):
                        st.write(myutils.ask_ollama(myutils.build_restock_prompt(low)))
                except Exception:
                    st.error("Could not reach Ollama. Make sure it is running and the model is installed.")

# download button, and auto-save so books survive a refresh
with st.sidebar:
    st.download_button("Download inventory CSV", st.session_state["inventory"].to_csv(index=False), "inventory.csv", "text/csv")
    myutils.save_inventory(st.session_state["inventory"])