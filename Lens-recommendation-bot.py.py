import gradio as gr
import os
from openai import OpenAI


def wait_for_run_completion(client, thread_id, run_id):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        print(f"Current run status: {run.status}")
        if run.status in ['completed', 'failed']:
            return run
            
def chatbot(path: str, prompt, api_key):
    client = OpenAI(api_key=api_key)


    file = client.files.create(
        file=open(path, "rb"),
        purpose='assistants'
        )
    assistant = client.beta.assistants.create(
    instructions="""
                
        - You are expert in Data Science. You will analyze the .csv files using Python and answer user's question from the uplaoded csv file. User will provide you information related to eye sight or lens and you have to recommend the best fitted product lens from the available data in .csv file. Keep in mind you will answer the query in Dutch Language.
        
        - The dataset contains 179 entries and 16 columns. Below is a detailed summary of each column, including its datatype and structure:
1. **Unnamed: 0**
   - **Description**: An index column that appears to be a simple sequential identifier for each row.
   - **Datatype**: `int64`
   - **Structure**: Contains integer values from 0 to 178.
2. **Product id**
   - **Description**: A unique identifier for each product.
   - **Datatype**: `int64`
   - **Structure**: Contains integer values representing product IDs.
3. **List price**
   - **Description**: The price of the product listed in the dataset.
   - **Datatype**: `float64`
   - **Structure**: Contains floating-point numbers representing the price.
4. **Category**
   - **Description**: The category to which the product belongs (e.g., contact lenses, lens solutions).
   - **Datatype**: `object`
   - **Structure**: Contains string values representing product categories.
5. **Product name**
   - **Description**: The name of the product.
   - **Datatype**: `object`
   - **Structure**: Contains string values representing product names.
6. **Features**
   - **Description**: Additional features or specifications of the product including Manufacturer name, Wearing time, Lens type, Material, and Brand name e.g., Fabrikant: Alcon; Draagtijd: Daglenzen; Type lens: Sferisch; Materiaal: Hydrogel; Brand Weblens: Freshlook
   - **Datatype**: `object`
   - **Structure**: Contains string values, but some entries are missing (NaN).
7. **Quantity**
   - **Description**: The quantity of the product available.
   - **Datatype**: `int64`
   - **Structure**: Contains integer values representing the quantity.
8. **Description**
   - **Description**: A detailed description of the product.
   - **Datatype**: `object`
   - **Structure**: Contains string values, but some entries are missing (NaN).
9. **Cyl**
   - **Description**: The cylinder value for astigmatism, if applicable.
   - **Datatype**: `object`
   - **Structure**: Contains string values, but only one entry is non-null.
10. **Sterkte**
    - **Description**: The strength (spherical value) of the lens.
    - **Datatype**: `object`
    - **Structure**: Contains string values representing different strength values, but many entries are missing (NaN).
11. **DIA**
    - **Description**: The diameter of the lens.
    - **Datatype**: `float64`
    - **Structure**: Contains floating-point numbers representing diameter values, with some entries missing (NaN).
12. **ADD**
    - **Description**: The addition value for multifocal lenses.
    - **Datatype**: `object`
    - **Structure**: Contains string values, but only a few entries are non-null.
13. **AX**
   - **Description**: The AX value represents the curvature of the lens, which is important for fitting contact lenses.
   - **Datatype**: `object`
   - **Structure**: Contains string values representing different curvature values, with some entries missing (NaN).
14. **BC**
   - **Description**: The BC value represents the base curve of the lens, which is crucial for ensuring proper fit and comfort.
   - **Datatype**: `object`
   - **Structure**: Contains string values representing different base curve values, with some entries having multiple values separated by commas.
15. **Popularity**
    - **Description**: A measure of the product's popularity, likely based on sales or ratings.
    - **Datatype**: `int64`
    - **Structure**: Contains integer values representing popularity scores.
16. **Image URL**
    - **Description**: A URL link to the product's image.
    - **Datatype**: `object`
    - **Structure**: Contains string values representing URLs.
17. **Product availability**
    - **Description**: Indicates whether the product is in stock or not.
    - **Datatype**: `object`
    - **Structure**: Contains string values indicating availability status.
18. **text**
    - **Description**: Additional text or information about the product.
    - **Datatype**: `object`
    - **Structure**: Contains string values providing further details about the product.
### Summary
- The dataset consists of various product-related information, including identifiers, pricing, specifications, and availability.
- The data types include integers, floating-point numbers, and strings (objects).
- Some columns have missing values, particularly in the features, description, and specific lens attributes (Cyl, Sterkte, DIA, ADD)
- Please keep in mind, while filtering a value in 'Category', 'Strekte', 'ADD', 'BC', 'Cyl', 'Features' and 'Description' columns instead of using `==` equal operator use `str.contains()` command to filter values.
- For brand name, Lens type, Manufacturer name and wearing time use `Features` column. 
        """
    ,
    model="gpt-4o",
    temperature=0,
    tools=[{"type": "code_interpreter"}],
    tool_resources={
        "code_interpreter": {
        "file_ids": [file.id]
        }
    }
    )
    
    assistant_id = assistant.id    
    thread = client.beta.threads.create()
 
    prompt = f"""{prompt}"""

    status = "na"
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Answer the user's query in Dutch on the basis of the data present in the .csv file: \n user's query: {prompt}",
        attachments= [
            {
            "file_id": file.id,
            "tools": [{"type": "code_interpreter"}]
            }
        ]
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,   
    )
    run = wait_for_run_completion(client, thread.id, run.id)
    while run.status == 'requires_action':
        print("Run requires action 1")
        run = wait_for_run_completion(client, thread.id, run.id)
    if run.status == 'failed':
        response = "Try Again!"
        return response

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value
    return response

default_user_prompt = "Wat is de populairste lens in de winkel?"
interface = gr.Interface(
    fn=chatbot,
    inputs=[
        gr.File(label="Upload CSV File"),
        gr.Textbox(lines=2, label="Enter your prompt", value=default_user_prompt),
        gr.Textbox(label="Enter your API key", type="password")
    ],
    outputs="markdown",
    title="Lens Recommendation Chatbot"
)

interface.launch()