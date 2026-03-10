import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { DocumentPublic } from 'src/models/document-models';

export interface DocumentCreatePayload {
  document_type: string;
  expiry_date: string; 
  notes?: string;
  machine_id?: number;
  operator_id?: number;
  file: File;
}

export const useDocumentStore = defineStore('document', {
  state: () => ({
    documents: [] as DocumentPublic[],
    isLoading: false,
  }),

  actions: {

    async fetchDocuments() {
      this.isLoading = true;
      try {
        const response = await api.get<DocumentPublic[]>('/documents/');
        this.documents = response.data;
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Falha ao carregar documentos.' });
        console.error('Erro ao buscar documentos:', error);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     *
     * @param payload
     */
    async createDocument(payload: DocumentCreatePayload) {
      this.isLoading = true;
      try {
        const formData = new FormData();

        formData.append('document_type', payload.document_type);
        formData.append('expiry_date', payload.expiry_date);
        if (payload.notes) formData.append('notes', payload.notes);
        if (payload.machine_id) formData.append('machine_id', String(payload.machine_id));
        if (payload.operator_id) formData.append('operator_id', String(payload.operator_id));
        
        formData.append('file', payload.file);

        const response = await api.post<DocumentPublic>('/documents/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        this.documents.unshift(response.data);
        Notify.create({ type: 'positive', message: 'Documento salvo com sucesso!' });

      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao salvar documento.' });
        console.error('Erro ao criar documento:', error);
        throw error; 
      } finally {
        this.isLoading = false;
      }
    },

    /**
     *
     * @param documentId
     */
    async deleteDocument(documentId: number) {
      this.isLoading = true;
      try {
        await api.delete(`/documents/${documentId}`);
        const index = this.documents.findIndex(doc => doc.id === documentId);
        if (index !== -1) {
          this.documents.splice(index, 1);
        }
        Notify.create({ type: 'positive', message: 'Documento removido com sucesso!' });
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Falha ao remover documento.' });
        console.error('Erro ao remover documento:', error);
      } finally {
        this.isLoading = false;
      }
    },
  },
});
