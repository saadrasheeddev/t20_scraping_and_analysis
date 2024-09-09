def find_date(html_content, index):
    for i in range(3):
        date_div = html_content[index].find('div', class_='ds-w-24')
        if date_div:
            date = date_div.text
            if date:
                return date
        index -= 1
    return "Date not found"