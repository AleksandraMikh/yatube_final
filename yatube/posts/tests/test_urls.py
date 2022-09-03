
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from ..models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # parameters which will be used in code several times
        cls.test_slug = "test-group"
        cls.test_author = 'TestAuthor'

        cls.author = User.objects.create(username=cls.test_author)
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug=cls.test_slug
        )
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

        self.authorized_client = Client()
        self.user = User.objects.create(username='TestUser')
        self.authorized_client.force_login(self.user)

        self.authorized_author = Client()
        self.authorized_author.force_login(PostURLTests.author)

    def test_pages_available_for_guests(self):
        post_id = str(PostURLTests.post.id)
        expected_codes = {
            '/': HTTPStatus.OK,
            '/group/' + PostURLTests.test_slug + '/': HTTPStatus.OK,
            '/profile/' + PostURLTests.test_author + '/': HTTPStatus.OK,
            '/posts/' + post_id + '/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }

        for url, expected_code in expected_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_code)

    def test_pages_available_for_authorized_only(self):
        url_expected_response = {
            '/create/':
            HTTPStatus.OK,
            '/posts/' + str(PostURLTests.post.id) + '/edit/':
            HTTPStatus.OK,
            '/posts/' + str(PostURLTests.post.id) + '/comment/':
            HTTPStatus.FOUND,
            '/follow/':
            HTTPStatus.OK,
            '/profile/' + PostURLTests.test_author + '/follow/':
            HTTPStatus.FOUND,
            '/profile/' + PostURLTests.test_author + '/unfollow/':
            HTTPStatus.FOUND,
        }
        for url, expected_response in url_expected_response.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, expected_response)
                response = self.guest_client.get(url)
                self.assertRedirects(response, '/auth/login/?next=' + url)

    # redirects:
    # test_create_post_not_available_for_guest,
    # test_edit_post_not_available_for_guest
    def test_forms_not_available_for_guest(self):
        # {start url : finish url}
        post_id = str(PostURLTests.post.id)
        redirects = {
            '/create/':
            '/auth/login/?next=/create/',
            f'/posts/{post_id}/edit/':
            f'/auth/login/?next=/posts/{post_id}/edit/',
            f'/posts/{post_id}/comment/':
            f'/auth/login/?next=/posts/{post_id}/comment/',
        }
        for start, finish in redirects.items():
            with self.subTest(redir_from=start):
                response = self.guest_client.get(start)
                self.assertRedirects(response, finish)

    def test_edit_post_not_available_for_autorized_not_author(self):
        post_id = str(PostURLTests.post.id)
        response = self.authorized_client.get('/posts/' + post_id + '/edit/')
        self.assertRedirects(response, '/posts/' + post_id + '/')

    def test_urls_uses_correct_template(self):
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/' + PostURLTests.test_slug + '/':
            'posts/group_list.html',
            '/profile/' + PostURLTests.test_author + '/':
            'posts/profile.html',
            '/posts/' + str(PostURLTests.post.id) + '/':
            'posts/post_detail.html',
            '/posts/' + str(PostURLTests.post.id) + '/edit/':
            'posts/create_post.html',
            '/create/':
            'posts/create_post.html',

        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
