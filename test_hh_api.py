import requests
import unittest

class TestHHApiFunctionalPositive(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestHHApiFunctionalPositive, self).__init__(*args, **kwargs)
        self.url = "https://api.hh.ru/vacancies"

    def _get_vacancies(self, params):
        response =  requests.get(self.url, params={'text': params})
        return response.json()['items']

    def _get_list_of_str_vacancies(self, vacancies):
        result = []
        words_for_removal = ['<highlighttext>', '</highlighttext>']
        for vacancy in vacancies:
            vacancy = str(vacancy).lower()
            for word in words_for_removal:
                vacancy = vacancy.replace(word, '')
            result.append(vacancy)
        return result

    def test_smoke(self):
        response = requests.get(self.url)
        self.assertEqual(response.status_code, requests.status_codes.codes.ok)

    def test_one_word_search_should_be_in_vacancy(self):
        word_for_search = 'программист'
        vacancies = self._get_vacancies(word_for_search)
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertIn(word_for_search, str(vacancy).lower())

    def test_two_word_search_both_in_vacancy(self):
        phrase_for_search = 'директор магазина'
        vacancies = self._get_vacancies(phrase_for_search)
        words = phrase_for_search.split()
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            for word in words:
                self.assertIn(word, vacancy)

    def test_search_phrase_in_quotes_should_be_near(self):
        phrase_for_search = "директор магазина"
        vacancies = self._get_vacancies('"{}"'.format(phrase_for_search))
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertRegex(str(vacancy).lower(), 'директор.{0,2}\sмагазин.{0,2}')


    def test_search_of_different_forms_of_the_term(self):
        vacancies = self._get_vacancies('продажи')
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            if 'продажи' not in vacancy:
                self.assertIn('продаж', vacancy)

    def test_search_only_particular_form(self):
        vacancies = self._get_vacancies('!продажи')
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertIn('продажи', vacancy)

    def test_search_with_star_symbol(self):
        vacancies = self._get_vacancies('Гео*')
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertRegex(vacancy, 'гео*')








if __name__ == '__main__':
    unittest.main()
