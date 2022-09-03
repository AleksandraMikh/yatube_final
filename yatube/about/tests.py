from django.test import TestCase, Client


class TestStatic(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_static_available(self):
        expexted_responses = {
            '/about/author/': 200,
            '/about/tech/': 200
        }
        for url, expexted_response in expexted_responses.items():
            with self.subTest(url=url):
                response = TestStatic.guest_client.get(url)
                self.assertEqual(response.status_code, expexted_response)

    def test_static_templates(self):
        expexted_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, expexted_template in expexted_templates.items():
            with self.subTest(url=url):
                response = TestStatic.guest_client.get(url)
                self.assertTemplateUsed(response, expexted_template)
