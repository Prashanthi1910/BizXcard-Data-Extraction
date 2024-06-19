import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import mysql.connector


def image_to_text(path):

  input_img=Image.open(io.BytesIO(path))

  #converting image to array format
  image_arr=np.array(input_img)

  reader=easyocr.Reader(['en'])
  text=reader.readtext(image_arr,detail=0)

  return text, input_img



def extracted_text(texts):

  extrd_dict={"NAME":[], "DESIGNATION":[], "COMPANY_NAME":[], "CONTACT":[],
              "EMAIL":[], "WEBSITE":[], "ADDRESS":[], "PINCODE":[]}
  extrd_dict["NAME"].append(texts[0])
  extrd_dict["DESIGNATION"].append(texts[1])

  for i in range(2, len(texts)):

    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):

      extrd_dict["CONTACT"].append(texts[i])

    elif "@" in texts[i] and ".com" in texts[i]:
      extrd_dict["EMAIL"].append(texts[i])

    elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
      small= texts[i].lower()
      extrd_dict["WEBSITE"].append(small)

    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extrd_dict["PINCODE"].append(texts[i])

    elif re.match(r'^[A-Za-z]', texts[i]):
      extrd_dict["COMPANY_NAME"].append(texts[i])

    else:
      remove_colon=re.sub(r'[,:]','',texts[i])
      extrd_dict["ADDRESS"].append(remove_colon)

  for key, value in extrd_dict.items():
    if len(value)>0:
      concatenate=" ".join(value)
      extrd_dict[key]=[concatenate]
    else:
      value="NA"
      extrd_dict[key]=[value]

  return extrd_dict



st.set_page_config(layout= "wide")
st.title("EXTRACT BUSINESS CARD DATA WITH 'OCR'")

with st.sidebar:
  select=option_menu("Main Menu", ["Home", "Upload & Modifying", "Delete"])

if select =="Home":
  st.markdown(
    "<h1 style='font-family:Arial; color:blue; font-size:40px;'>BIZCARD DATA EXTRACTION USING EASYOCR, PANDAS, SQL</h1>",
    unsafe_allow_html=True)

elif select == "Upload & Modifying":
  img = st.file_uploader("Upload the Image", type=["png", "jpg", "jpeg"])
  if img is not None:
    image= Image.open(img)
    st.image(image, caption="Uploaded Image", use_column_width= True)


    img_data=img.getvalue()
    text_img, input_img= image_to_text(img_data)
   

    text_dict= extracted_text(text_img)

    image_bytes= text_dict
    image_bytes['IMAGE BYTES']=[img_data]

    df= pd.DataFrame(image_bytes)

    if text_dict:
      st.success("TEXT IS EXTRACTED SUCCESSFULLY")

    df= pd.DataFrame(text_dict)

    st.dataframe(df)

    

    button_1= st. button("Save", use_container_width=True)

    if button_1:
      mydb = mysql.connector.connect(
      host='localhost',
      user='root',
      password='Prashanthi@19',
      database='bizcardx')
    

      cursor = mydb.cursor()

      create_table = ''' 
      CREATE TABLE IF NOT EXISTS bizcardx_details (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(225),
          designation VARCHAR(225),
          company_name VARCHAR(225),
          contact VARCHAR(225),
          email VARCHAR(225),
          website VARCHAR(225),
          address VARCHAR(225),
          pincode VARCHAR(225),
          image_bytes LONGBLOB
      );
      '''
      cursor.execute(create_table)

      insert_query = '''
              INSERT INTO bizcardx_details (
                  name, designation, company_name, contact, email, website, address, pincode, image_bytes
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
              '''
        
      values = (
        text_dict['NAME'][0], text_dict['DESIGNATION'][0], text_dict['COMPANY_NAME'][0],
        text_dict['CONTACT'][0], text_dict['EMAIL'][0], text_dict['WEBSITE'][0],
        text_dict['ADDRESS'][0], text_dict['PINCODE'][0], img_data
      )

      datas= df.values.tolist()[0]
      cursor.execute(insert_query, datas)
      mydb.commit()


      st.success("SAVED SUCCESSFULLY")
  method= st.radio("Select the Method",["None","preview", "Modify"])

  if method== "preview":

    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Prashanthi@19',
            database='bizcardx')

    cursor = mydb.cursor()
    select_query = "SELECT name, designation, company_name, contact, email, website, address, pincode, image_bytes FROM bizcardx_details"

    cursor.execute(select_query)
    table = cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT",
                                            "EMAIL", "WEBSITE", "ADDRESS",
                                            "PINCODE", "IMAGE"))
    st.dataframe(table_df)

  elif method == "Modify":
    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Prashanthi@19',
            database='bizcardx')

    cursor = mydb.cursor()
    select_query = "SELECT name, designation, company_name, contact, email, website, address, pincode, image_bytes FROM bizcardx_details"

    cursor.execute(select_query)
    table = cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT",
                                            "EMAIL", "WEBSITE", "ADDRESS",
                                            "PINCODE", "IMAGE"))
    
    col1, col2= st.columns(2)
    with col1:
      selected_name= st.selectbox("Select the name", table_df["NAME"])
    
    df_3= table_df[table_df["NAME"]== selected_name]

    df_4=df_3.copy()
    st.dataframe(df_4)

    col1, col2= st.columns(2)
    with col1:
      mo_name= st.text_input("Name", df_3["NAME"].unique()[0])
      mo_desi= st.text_input("Designation", df_3["DESIGNATION"].unique()[0])
      mo_com_name= st.text_input("Comapany_name", df_3["COMPANY_NAME"].unique()[0])
      mo_contact= st.text_input("Contact", df_3["CONTACT"].unique()[0])
      mo_email= st.text_input("Email", df_3["EMAIL"].unique()[0])

    with col2:
      mo_website= st.text_input("Website", df_3["WEBSITE"].unique()[0])
      mo_addre= st.text_input("Address", df_3["ADDRESS"].unique()[0])
      mo_pincode= st.text_input("Pincode", df_3["PINCODE"].unique()[0])
      mo_image= st.text_input("Image", df_3["IMAGE"].unique()[0])

      df_4["WEBSITE"]= mo_website
      df_4["ADDRESS"]= mo_addre
      df_4["PINCODE"]= mo_pincode
      df_4["IMAGE"]= mo_image
    
    st.dataframe(df_4)

    col1, col2=st.columns(2)
    with col1:
      button_3=st.button("Modify", use_container_width=True)

    if button_3:
      mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Prashanthi@19',
            database='bizcardx')

      cursor = mydb.cursor()

      cursor.execute(f"DELETE from bizcardx_details WHERE NAME='{selected_name}'")
      mydb.commit()

      insert_query = '''
              INSERT INTO bizcardx_details (
                  name, designation, company_name, contact, email, website, address, pincode, image_bytes
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
              '''

      datas= df_4.values.tolist()[0]
      cursor.execute(insert_query, datas)
      mydb.commit()

      st.success("MODIFIED SUCCESSFULLY")
      
   
   
elif select == "Delete":
  
  mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Prashanthi@19',
            database='bizcardx')

  cursor = mydb.cursor()

  col1,col2=st.columns(2)
  with col1:

    select_query = "SELECT name FROM bizcardx_details"

    cursor.execute(select_query)
    table1 = cursor.fetchall()
    mydb.commit()

    names=[]

    for i in table1:
      names.append(i[0])

    name_select=st.selectbox("Select the name", names)

  with col2:
    select_query = f"SELECT designation FROM bizcardx_details where name='{name_select}'"

    cursor.execute(select_query)
    table2 = cursor.fetchall()
    mydb.commit()

    designation=[]

    for j in table2:
      designation.append(j[0])

    designation_select=st.selectbox("Select the designation", designation)

  if name_select and designation_select:
    col1, col2, col3= st.columns(3)

    with col1:
      st.write(f"Selected Name : {name_select}")
      st.write("")
      st.write("")
      st.write("")
      st.write(f"Selected Designation : {designation_select}")

    with col2:
      st.write("")
      st.write("")
      st.write("")
      st.write("")

      remove = st.button("Delete", use_container_width=True)

      if remove:
        cursor.execute(f"DELETE from bizcardx_details WHERE NAME='{name_select}' AND DESIGNATION='{designation_select}'")
        mydb.commit()

        st.warning("DELETED")
