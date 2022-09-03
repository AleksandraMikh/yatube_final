from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Post, Group

User = get_user_model()

# Create your tests here.


class TestCaseModels(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_title = 'Длинное тестовове название'
        cls.test_text = 'Это длинный-длинный тестовый пост'
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title=cls.test_title,
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text=cls.test_text,
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        group = TestCaseModels.group
        post = TestCaseModels.post

        strs_for_models = {
            group: TestCaseModels.test_title,
            post: TestCaseModels.test_text[:15]
        }
        for model_inst, str_text in strs_for_models.items():
            with self.subTest(model=model_inst.__class__.__name__):
                self.assertEqual(str(model_inst), str_text)
