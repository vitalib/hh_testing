import random
import requests
import string
import unittest


class TestHHApiFunctional(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestHHApiFunctional, self).__init__(*args, **kwargs)
        self.url = "https://api.hh.ru/vacancies"

    def _get_vacancies(self, params):
        response = requests.get(self.url, params={'text': params})
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


class TestHHApiFunctionalPositive(TestHHApiFunctional):
    def __init__(self, *args, **kwargs):
        super(TestHHApiFunctionalPositive, self).__init__(*args, **kwargs)

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
            self.assertRegex(
                str(vacancy).lower(),
                r'директор.{0,2}\sмагазин.{0,2}'
            )

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

    def test_search_synonymus_of_term(self):
        vacancies = self._get_vacancies('пиарщик')
        vacancies_with_syn = [
            item for item in self._get_list_of_str_vacancies(vacancies)
                if 'пирщик' not in item
        ]
        self.assertTrue(any('pr-менеджер' in item
            for item in vacancies_with_syn))

    def test_search_for_one_of_the_words_if_with_OR(self):
        vacancies = self._get_vacancies('столяр OR плотник')
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertTrue('столяр' in vacancy or 'плотник' in vacancy)

    def test_search_of_all_words_with_AND(self):
        first_term = "холодильное оборудование"
        second_term = "торговое оборудование"
        vacancies = self._get_vacancies('"{}" AND "{}"'.format(
            first_term,
            second_term
        ))
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertRegex(vacancy, r'холодильн.{2,4}\s*оборудовани.{1,3}')
            self.assertRegex(vacancy, r'торгов.* оборудовани.{1,3}')

    def test_exclude_term_from_search(self):
        first_term, second_term, third_term = 'столяр', 'плотник', 'электрик'
        vacancies = self._get_vacancies('{} NOT {} NOT {}'.format(
            first_term, second_term, third_term
        ))
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertIn(first_term, vacancy)
            self.assertNotIn(second_term, vacancy)
            self.assertNotIn(third_term, vacancy)

    def test_join_conditions_with_parentheses(self):
        first, second = 'столяр', 'столяр-плотник'
        third, fourth = 'электрик', 'сантехник'
        search_query = '({} OR {}) AND ({} OR {})'.format(
            first, second, third, fourth
        )
        vacancies = self._get_vacancies(search_query)
        for vacancy in self._get_list_of_str_vacancies(vacancies):
            self.assertTrue(any(item in vacancy for item in (first, second)))
            self.assertTrue(any(item in vacancy for item in (third, fourth)))

    def test_serarh_in_fields(self):
        vacancies = self._get_vacancies(
            'NAME:(python OR java) and COMPANY_NAME:HeadHunter'
        )
        for vacancy in vacancies:
            self.assertTrue(
                any(item in vacancy['name'].lower()
                    for item in ('python', 'java'))
            )
            self.assertIn('HeadHunter', vacancy['employer']['name'])


class TestHHApiFunctionalSecurity(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestHHApiFunctionalSecurity, self).__init__(*args, **kwargs)
        self.url = "https://api.hh.ru/vacancies"

    def test_sql_injection(self):
        response = requests.get(self.url, params={'text':
            "столяр+UNION+SELECT+*+FROM+accounts"
        })
        self.assertEqual(response.status_code, 200)
        vacancies_found = response.json()['found']
        self.assertEqual(vacancies_found, 0)

    def test_html_injection(self):
        response = requests.get(
            self.url,
            params={'text':
            "<h1>Hello World</h1>"
            }
        )
        self.assertEqual(response.status_code, 200)
        vacancies_found = response.json()['found']
        self.assertEqual(vacancies_found, 0)
        self.assertNotIn('<h1>Hello World</h1>', response.text)

    def test_huge_input(self):
        response = requests.get(self.url, params={'text':
            ''.join(random.choice(string.printable) for _ in range(10**6))
        })
        self.assertEqual(response.status_code, 414)


class TestHHApiFunctionalNegative(TestHHApiFunctional):
    def __init__(self, *args, **kwargs):
        super(TestHHApiFunctionalNegative, self).__init__(*args, **kwargs)

    def test_incorrect_input_returns_no_vacancies(self):
        word_for_search = 'абрашвабракадабра'
        vacancies = self._get_vacancies(word_for_search)
        self.assertEqual(len(vacancies), 0)

    def test_incorrect_fields_names_returns_no_vacancies(self):
        vacancies = self._get_vacancies(
            'NAMES:(python OR java) and COMPANY_NAMES:HeadHunter'
        )
        self.assertEqual(len(vacancies), 0)


if __name__ == '__main__':
    unittest.main()
