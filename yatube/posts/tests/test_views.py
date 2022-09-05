# from asyncio.windows_events import NULL
import shutil
import tempfile


from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from ..models import Group, Post, Follow
from ..forms import PostForm, CommentForm
from django.urls import reverse
from ..settings import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TemplatesAndContextTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # parameters which will be used in code several times
        cls.test_slug = "test-group"
        cls.test_username = 'TestUser'

        cls.user = User.objects.create(username=cls.test_username)
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug=cls.test_slug,
            description='test description'
        )

        cls.first_post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.user,
            group=cls.group
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
            content_type='image/gif'
        )
        cls.latest_post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(
            TemplatesAndContextTests.user)

    def test_views_render_correct_templates(self):
        url_templates_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:follow_index'):
            'posts/follow.html',
            reverse('posts:group',
                    kwargs={'slug':
                            TemplatesAndContextTests.test_slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            TemplatesAndContextTests.test_username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            TemplatesAndContextTests.latest_post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            str(TemplatesAndContextTests.latest_post.id)}):
            'posts/create_post.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, TemplatesAndContextTests.user)
        self.assertEqual(
            post.pub_date, TemplatesAndContextTests.latest_post.pub_date)
        self.assertEqual(post.text, TemplatesAndContextTests.latest_post.text)
        self.assertEqual(
            post.group, TemplatesAndContextTests.latest_post.group)
        self.assertEqual(
            post.image, TemplatesAndContextTests.latest_post.image)
        self.assertEqual(
            post.image.name, 'posts/' + TemplatesAndContextTests.uploaded.name
        )

    def test_context_posts_index(self):
        url = reverse('posts:index')
        response = self.client.get(url)
        self.check_context_contains_page_or_post(response.context)

    def test_context_posts_group(self):
        url = reverse('posts:group',
                      kwargs={'slug':
                              TemplatesAndContextTests.test_slug})
        response = self.client.get(url)
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, TemplatesAndContextTests.group.title)
        self.assertEqual(group.description,
                         TemplatesAndContextTests.group.description)

    def test_context_posts_profile(self):
        url = reverse('posts:profile',
                      kwargs={'username':
                              TemplatesAndContextTests.test_username})
        response = self.client.get(url)
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('author', response.context)
        self.assertEqual(
            response.context['author'], TemplatesAndContextTests.user)

    def test_context_posts_detail(self):
        url = reverse('posts:post_detail',
                      kwargs={'post_id':
                              TemplatesAndContextTests.latest_post.id})
        response = self.client.get(url)
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

    # check context in views containig PostForms
    def test_context_forms(self):
        urls = [
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            str(TemplatesAndContextTests.latest_post.id)}),
            reverse('posts:post_create')
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

                self.assertIn('is_edit', response.context)
                is_edit = response.context['is_edit']
                self.assertIsInstance(is_edit, bool)
                self.assertEqual(is_edit, bool(
                    url != reverse('posts:post_create')))


class PaginatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # parameters which will be used in code several times
        cls.test_slug = "test-group"
        cls.test_username = 'TestUser'

        cls.user = User.objects.create(username=cls.test_username)
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug=cls.test_slug
        )

    def setUp(self):
        cache.clear()
        self.client = Client()

    # check two pages of paginator
    def test_paginator(self):
        initial_length = Post.objects.count()
        extra_posts = POSTS_PER_PAGE + 3
        second_page = (initial_length + extra_posts) // POSTS_PER_PAGE

        posts = [
            Post(
                text="Тестовый текст поста номер" + str(i),
                author=PaginatorTest.user,
                group=PaginatorTest.group
            )
            for i in range(1, POSTS_PER_PAGE + second_page + 1)
        ]

        Post.objects.bulk_create(posts)

        urls = {
            reverse('posts:index'),
            reverse('posts:group',
                    kwargs={'slug':
                            PaginatorTest.test_slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            PaginatorTest.test_username}),
        }

        pages = {
            1: POSTS_PER_PAGE,
            2: second_page
        }

        for url in urls:
            for page, length in pages.items():
                with self.subTest(url=url, page=page):
                    response = self.client.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context['page_obj']), length)


class TrackGroupOfPost(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # parameters which will be used in code several times
        cls.test_slug_1 = "test-group-1"
        cls.test_slug_2 = "test-group-2"

        cls.user = User.objects.create(username='TestUser')
        cls.group_1 = Group.objects.create(
            title="Тестовое название группы 1",
            slug=cls.test_slug_1
        )

        cls.group_2 = Group.objects.create(
            title="Тестовое название группы 2",
            slug=cls.test_slug_2
        )

        cls.post_from_group_1 = Post.objects.create(
            text="Тестовый текст поста 1",
            author=cls.user,
            group=cls.group_1
        )

        cls.post_from_group_2 = Post.objects.create(
            text="Тестовый текст поста 2",
            author=cls.user,
            group=cls.group_2
        )

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(
            TrackGroupOfPost.user)

    # check that post from group2 doesn't appear
    # on page with group1 posts
    def test_group_track(self):
        # get response from page with group1 posts
        url = reverse('posts:group',
                      kwargs={'slug':
                              TrackGroupOfPost.test_slug_1})
        response = self.authorized_client.get(url)
        with self.subTest(
                group_of_post=TrackGroupOfPost.group_2):
            # check that no post from group1 page equals
            # to post from group2 page
            self.assertNotIn(TrackGroupOfPost.post_from_group_2,
                             response.context['page_obj'])

# I implemented test which checks
#  - if cache works
#  - how large is the cache period
# Ultimate drawback of this test is 20 seconds sleep function


class Cache(TestCase):

    def setUp(self):
        cache.clear()

    def test_index_cached(self):

        # create post
        user = User.objects.create(username='TestUser')
        post = Post.objects.create(
            text='Test text',
            author=user,)

        # get response when post created
        guest_client = Client()
        response = guest_client.get(reverse('posts:index'))
        cashed_response_start = response.content

        # check that post was created in db
        count = Post.objects.count()
        self.assertEqual(1, count)

        # delete post
        post.delete()

        # check that new post is still in response
        response = guest_client.get(reverse('posts:index'))
        self.assertEqual(cashed_response_start,
                         response.content)

        # clear cash and get new response
        # check that new response differs from cashed initially
        cache.clear()
        response = guest_client.get(reverse('posts:index'))
        self.assertNotEqual(cashed_response_start,
                            response.content)

        # check that new post is not in the context
        posts = response.context['page_obj']
        self.assertNotIn(post, posts)


class FollowTests(TestCase):

    def setUp(self):
        # parameters to be used in many pieces of code
        self.authorname = 'TestAuthorname'

        cache.clear()
        self.author = User.objects.create(username=self.authorname)
        self.user = User.objects.create(username='TestUsername')
        self.authorised_client = Client()
        self.authorised_client.force_login(user=self.user)

    def test_authorized_can_follow(self):
        self.authorised_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.authorname}))
        count = Follow.objects.filter(user=self.user).count()
        self.assertEqual(1, count)
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.author).exists())

    def test_authorized_can_unfollow(self):
        Follow.objects.create(user=self.user,
                              author=self.author)
        self.authorised_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.authorname}))
        count = Follow.objects.filter(user=self.user).count()
        self.assertEqual(0, count)
        self.assertFalse(Follow.objects.filter(user=self.user,
                                               author=self.author).exists())

    def test_new_post_in_follow_index_only(self):
        # parameters to be used in many pieces of code
        text = 'Тестовый тескст поста'

        Follow.objects.create(user=self.user,
                              author=self.author)
        new_post = Post.objects.create(
            text=text,
            author=self.author
        )

        # new post in follow index of follower
        response = self.authorised_client.get(reverse('posts:follow_index'))
        self.assertIn(new_post, response.context['page_obj'])

        # new post is not in follow index of not followers
        # make author not to follow himself and check his follow index
        authorised_author = Client()
        authorised_author.force_login(user=self.author)
        Follow.objects.filter(user=self.author,
                              author=self.author).delete()
        response = authorised_author.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context['page_obj'])
