from django.db import models


class ExplanationHistory(models.Model):
    title = models.CharField(max_length=120)
    language = models.CharField(max_length=24, default="python")
    code = models.TextField()
    problem = models.TextField(blank=True)
    result = models.JSONField()
    sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "explanation history"

    def __str__(self):
        return self.title
