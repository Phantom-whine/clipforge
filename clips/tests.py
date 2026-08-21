from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Clip, Project


class ProjectDeletionTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.project = Project.objects.create(
			name='Delete me',
			original_file=SimpleUploadedFile('source.mp4', b'video data', content_type='video/mp4'),
			file_type='mp4',
		)
		Clip.objects.create(
			project=self.project,
			title='Extracted clip',
			start_time=0,
			end_time=5,
			duration=5,
			why_this_clip='A useful moment',
			hook_strength=80,
			curiosity=80,
			standalone=80,
			value=80,
			entertainment=80,
			overall_score=80,
			clip_file=SimpleUploadedFile('clip.mp4', b'clip data', content_type='video/mp4'),
		)

	def test_delete_project_removes_project_and_clips(self):
		response = self.client.delete(f'/api/projects/{self.project.id}/')

		self.assertEqual(response.status_code, 204)
		self.assertFalse(Project.objects.filter(id=self.project.id).exists())
		self.assertFalse(Clip.objects.filter(project_id=self.project.id).exists())
