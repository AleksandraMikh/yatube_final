import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Post, Group, Comment
from django.contrib.auth import get_user_model
from django.urls import reverse
from http import HTTPStatus

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.author = User.objects.create(
            username='TestUser'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.author)

    def test_new_post_form(self):
        post_text = 'Текст поста из формы'
        form_data = {
            'text': post_text,
            'group': PostFormTest.group.id,
            'image': PostFormTest.uploaded
        }

        url = reverse('posts:post_create')
        response = self.authorized_client.post(
            url, data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, post_text)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, PostFormTest.group)
        self.assertEqual(post.image.name, 'posts/'
                         + PostFormTest.uploaded.name)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_form(self):
        post = Post.objects.create(
            text='test',
            author=self.author,
            group=PostFormTest.group
        )
        new_post_text = 'new text'
        new_group = Group.objects.create(
            title='New Test group',
            slug='new-test-group',
            description='new test description'
        )

        url = reverse('posts:post_edit', kwargs={
                      'post_id': post.id})
        form_data = {
            'text': new_post_text,
            'group': new_group.id
        }
        self.authorized_client.post(
            url, data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), 1)
        new_post = Post.objects.first()
        self.assertEqual(
            new_post.text, new_post_text)
        self.assertEqual(
            new_post.group, new_group)

        old_group_response = self.authorized_client.get(
            reverse('posts:group', args=(self.group.slug,))
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 0)

    def test_unauth_user_cant_publish_post(self):
        form_data = {
            'text': 'Текст нежелательного поста',
            'group': PostFormTest.group.id
        }

        url = reverse('posts:post_create')
        guest_client = Client()
        response = guest_client.post(
            url, data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), 0)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + url)


class CommentsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(
            CommentsTests.user)
        self.guest_client = Client()

    def test_unauth_user_cant_comment(self):
        form_data = {
            'text': 'Текст нежелательного комментария',
        }

        url = reverse('posts:post_detail', args=[CommentsTests.post.id])
        guest_client = Client()
        response = guest_client.post(
            url, data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_form(self):
        comment_text = 'Текст поста из формы'
        form_data = {
            'text': comment_text,
        }

        url = reverse('posts:add_comment', args=[CommentsTests.post.id])
        response = self.authorized_client.post(
            url, data=form_data
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, comment_text)
        self.assertEqual(comment.author, CommentsTests.user)
        self.assertEqual(comment.post, CommentsTests.post)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[CommentsTests.post.id]))

        response = self.authorized_client.get(reverse(
            'posts:post_detail', args=[CommentsTests.post.id]))
        self.assertEqual(*response.context.get('comments').all(), comment)
