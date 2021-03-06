from questionnaire import Questionnaire

q = Questionnaire()
q.add_question('day', options=['monday', 'friday', 'saturday'])
q.add_question('time', options=['morning', 'night'])

# nights
q.add_question('activities', prompter='multiple', options=['eat tacos de pastor', 'go to the cantina', 'do some programming']).\
    add_condition(keys=['time'], vals=['night'])
# saturday morning
q.add_question('activities', prompter='multiple', options=['eat barbacoa', 'watch footy match', 'walk the dog']).\
    add_condition(keys=['day', 'time'], vals=['saturday', 'morning'])
# other mornings
q.add_question('activities', prompter='multiple', options=['eat granola', 'get dressed', 'go to work']).\
    add_condition(keys=['time'], vals=['morning'])

answers = q.run()
print(answers)
