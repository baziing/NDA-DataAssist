<template>
  <div class="email-container">
    <el-card class="email-card">
      <el-tabs v-model="activeTab">
        <!-- 邮箱管理标签页 -->
        <el-tab-pane label="邮箱管理" name="email">
          <div class="action-bar">
            <el-button type="primary" @click="showEmailModal">
              <i class="el-icon-plus" /> 添加邮箱
            </el-button>
            <el-input
              v-model="emailSearchText"
              placeholder="搜索邮箱"
              style="width: 250px; margin-left: 16px"
              clearable
              @keyup.enter.native="searchEmails"
            >
              <el-button slot="append" icon="el-icon-search" @click="searchEmails" />
            </el-input>
          </div>

          <el-table
            v-loading="loading"
            :data="emailList"
            border
            style="width: 100%"
          >
            <el-table-column prop="email" label="邮箱地址" min-width="180" />
            <el-table-column prop="groups" label="所属分组" min-width="200">
              <template slot-scope="scope">
                <el-tag
                  v-for="group in scope.row.groups"
                  :key="group.value"
                  size="small"
                  style="margin-right: 5px; margin-bottom: 5px;"
                >
                  {{ group.label }}
                </el-tag>
                <span v-if="!scope.row.groups || scope.row.groups.length === 0">无</span>
              </template>
            </el-table-column>
            <el-table-column prop="reports" label="接收报表" min-width="200">
              <template slot-scope="scope">
                <el-tag
                  v-for="report in scope.row.reports"
                  :key="report.id"
                  size="small"
                  type="success"
                  style="margin-right: 5px; margin-bottom: 5px;"
                >
                  {{ report.name }}
                </el-tag>
                <span v-if="!scope.row.reports || scope.row.reports.length === 0">无</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template slot-scope="scope">
                <el-button
                  type="text"
                  size="small"
                  @click="editEmail(scope.row)"
                >编辑</el-button>
                <el-divider direction="vertical" />
                <el-button
                  type="text"
                  size="small"
                  class="delete-btn"
                  @click="deleteEmail(scope.row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 删除确认对话框 -->
          <delete-confirmation-dialog
            :visible="deleteDialogVisible"
            :message="'此操作将永久删除该邮箱, 是否继续?'"
            :loading="loading"
            @confirm="handleConfirmDelete"
            @cancel="handleCancelDelete"
          />

          <!-- 邮箱表单弹窗 -->
          <el-dialog
            :title="emailFormMode === 'add' ? '添加邮箱' : '编辑邮箱'"
            :visible.sync="emailModalVisible"
            width="500px"
          >
            <el-form ref="emailFormRef" :model="emailForm" :rules="emailRules" label-width="100px">
              <el-form-item label="邮箱地址" prop="email">
                <el-input v-model="emailForm.email" placeholder="请输入邮箱地址" />
              </el-form-item>
              <el-form-item label="所属分组">
                <el-select
                  v-model="emailForm.groups"
                  multiple
                  collapse-tags
                  placeholder="请选择所属分组"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in groupOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="接收报表" prop="reports">
                <el-select
                  v-model="emailForm.reports"
                  multiple
                  collapse-tags
                  placeholder="请选择接收的报表"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in reportOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
              <el-button @click="emailModalVisible = false">取 消</el-button>
              <el-button type="primary" @click="handleEmailSubmit">确 定</el-button>
            </span>
          </el-dialog>
        </el-tab-pane>

        <!-- 邮箱组管理标签页 -->
        <el-tab-pane label="邮箱组管理" name="group">
          <div class="action-bar">
            <el-button type="primary" @click="showGroupModal">
              <i class="el-icon-plus" /> 添加邮箱组
            </el-button>
            <el-input
              v-model="groupSearchText"
              placeholder="搜索邮箱组"
              style="width: 250px; margin-left: 16px"
              clearable
              @keyup.enter.native="searchGroups"
            >
              <el-button slot="append" icon="el-icon-search" @click="searchGroups" />
            </el-input>
          </div>

          <el-table
            :data="groupList"
            border
            style="width: 100%"
          >
            <el-table-column prop="group_name" label="组名称" min-width="150" />
            <el-table-column prop="memberCount" label="成员数量" width="100" />
            <el-table-column prop="memberEmails" label="成员邮箱" min-width="500">
              <template slot-scope="scope">
                <div v-if="scope.row.memberEmails && scope.row.memberEmails.length > 0" class="member-emails-container">
                  <div class="member-emails-wrapper">
                    <el-tag
                      v-for="(email, index) in scope.row.memberEmails"
                      :key="index"
                      size="small"
                      class="member-email-tag"
                    >
                      {{ email }}
                    </el-tag>
                  </div>
                  <el-button
                    type="text"
                    size="small"
                    class="show-all-btn"
                    @click="viewAllMembers(scope.row)"
                  >
                    显示全部
                  </el-button>
                </div>
                <span v-else>无成员</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template slot-scope="scope">
                <el-button
                  type="text"
                  size="small"
                  @click="editGroup(scope.row)"
                >编辑</el-button>
                <el-divider direction="vertical" />
                <el-button
                  type="text"
                  size="small"
                  @click="manageGroupMembers(scope.row)"
                >管理成员</el-button>
                <el-divider direction="vertical" />
                <el-button
                  type="text"
                  size="small"
                  class="delete-btn"
                  @click="deleteGroup(scope.row.id)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 邮箱组表单弹窗 -->
          <el-dialog
            :title="groupFormMode === 'add' ? '添加邮箱组' : '编辑邮箱组'"
            :visible.sync="groupModalVisible"
            width="600px"
          >
            <el-form ref="groupFormRef" :model="groupForm" :rules="groupRules" label-width="100px">
              <el-form-item label="组名称" prop="name">
                <el-input v-model="groupForm.name" placeholder="请输入组名称" />
              </el-form-item>
              <el-form-item label="成员邮箱">
                <el-select
                  v-model="groupForm.members"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="请选择或输入成员邮箱"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in allEmailOptions"
                    :key="item.id"
                    :label="item.email"
                    :value="item.id"
                  />
                </el-select>
                <div class="form-tip">可以选择已有邮箱或直接输入新邮箱地址</div>
              </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
              <el-button @click="groupModalVisible = false">取 消</el-button>
              <el-button type="primary" @click="handleGroupSubmit">确 定</el-button>
            </span>
          </el-dialog>

          <!-- 邮箱组成员管理弹窗 -->
          <el-dialog
            title="管理邮箱组成员"
            :visible.sync="memberModalVisible"
            width="700px"
          >
            <el-transfer
              v-model="selectedEmailIds"
              :data="allEmails"
              :titles="['可选邮箱', '已选邮箱']"
              :button-texts="['移除', '添加']"
              :props="{
                key: 'id',
                label: 'email'
              }"
              @change="handleMemberChange"
            />
            <span slot="footer" class="dialog-footer">
              <el-button @click="memberModalVisible = false">取 消</el-button>
              <el-button type="primary" @click="handleMemberSubmit">确 定</el-button>
            </span>
          </el-dialog>

          <!-- 查看全部成员弹窗 -->
          <el-dialog
            title="全部成员邮箱"
            :visible.sync="allMembersVisible"
            width="600px"
          >
            <div class="all-members-list">
              <el-tag
                v-for="(email, index) in currentGroupMembers"
                :key="index"
                size="medium"
                style="margin: 5px;"
              >
                {{ email }}
              </el-tag>
            </div>
            <span slot="footer" class="dialog-footer">
              <el-button type="primary" @click="allMembersVisible = false">关闭</el-button>
            </span>
          </el-dialog>

          <!-- 邮箱组删除确认对话框 -->
          <delete-confirmation-dialog
            :visible="groupDeleteConfirmVisible"
            :message="'此操作将永久删除该邮箱组, 是否继续?'"
            :loading="loading"
            @confirm="confirmGroupDelete"
            @cancel="cancelGroupDelete"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import { getToken } from '@/utils/auth'
import DeleteConfirmationDialog from '@/components/DeleteConfirmationDialog.vue'

// 创建一个axios实例，设置基础URL和请求头
const apiClient = axios.create({
  // 直接使用完整的后端URL
  baseURL: 'http://localhost:5002',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 设置超时时间为30秒
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    const token = getToken()
    if (token) {
      config.headers['X-Token'] = token
    }
    return config
  },
  error => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response
  },
  error => {
    // 对响应错误做点什么
    console.error('响应错误:', error)
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    } else if (error.request) {
      // 请求已经发出，但没有收到响应
      console.error('没有收到响应:', error.request)
    } else {
      // 在设置请求时发生了一些事情，触发了错误
      console.error('请求配置错误:', error.message)
    }
    return Promise.reject(error)
  }
)

export default {
  name: 'EmailManagement',
  components: {
    DeleteConfirmationDialog
  },
  data() {
    return {
      activeTab: 'email',
      loading: false,

      // 邮箱管理
      emailList: [],
      emailSearchText: '',
      emailModalVisible: false,
      emailFormMode: 'add',
      emailForm: {
        id: null,
        email: '',
        groups: [],
        reports: []
      },
      emailRules: {
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
        ],
        reports: [
          { required: true, message: '请选择接收报表', trigger: 'change' }
        ]
      },

      // 删除确认
      deleteTargetId: null,
      deleteDialogVisible: false,

      // 邮箱组管理
      groupList: [],
      groupSearchText: '',
      groupModalVisible: false,
      groupFormMode: 'add',
      groupForm: {
        id: null,
        name: '',
        members: []
      },
      groupRules: {
        name: [
          { required: true, message: '请输入组名称', trigger: 'blur' }
        ]
      },

      // 邮箱组成员管理
      memberModalVisible: false,
      currentGroupId: null,
      allEmails: [],
      selectedEmailIds: [],

      // 查看全部成员
      allMembersVisible: false,
      currentGroupMembers: [],

      // 选项数据
      groupOptions: [],
      reportOptions: [],
      allEmailOptions: [],

      // 邮箱组删除确认
      groupDeleteConfirmVisible: false
    }
  },
  created() {
    this.fetchEmails()
    this.fetchGroups()
    this.fetchReportOptions()
  },
  methods: {
    // 邮箱管理方法
    fetchEmails() {
      this.loading = true
      apiClient.get('/emails')
        .then(response => {
          this.emailList = response.data.map(email => ({
            ...email,
            id: String(email.id),
            groups: email.groups ? email.groups.map(group => ({ ...group, value: String(group.value) })) : [],
            reports: email.reports ? email.reports.map(report => ({ ...report, id: String(report.id) })) : []
          }))
          // 更新邮箱选项
          this.allEmailOptions = this.emailList.map(item => ({
            id: item.id,
            email: item.email
          }))
          this.loading = false
        })
        .catch(error => {
          console.error('获取邮箱列表失败:', error)
          this.$message.error('获取邮箱列表失败')
          this.loading = false
        })
    },

    searchEmails() {
      this.loading = true
      apiClient.get(`/emails/search?q=${this.emailSearchText}`)
        .then(response => {
          this.emailList = response.data.map(email => ({
            ...email,
            id: String(email.id),
            groups: email.groups ? email.groups.map(group => ({ ...group, value: String(group.value) })) : [],
            reports: email.reports ? email.reports.map(report => ({ ...report, id: String(report.id) })) : []
          }))
          this.loading = false
        })
        .catch(error => {
          console.error('搜索邮箱失败:', error)
          this.$message.error('搜索邮箱失败')
          this.loading = false
        })
    },

    showEmailModal() {
      this.emailFormMode = 'add'
      this.emailForm = {
        id: null,
        email: '',
        groups: [],
        reports: []
      }
      this.emailModalVisible = true
    },

    editEmail(row) {
      this.emailFormMode = 'edit'
      this.emailForm = {
        id: String(row.id), // 将 row.id 转换为字符串
        email: row.email,
        groups: row.groups ? row.groups.map(g => g.value) : [],
        reports: row.reports ? row.reports.map(r => String(r.id)) : [] // 将 report ID 转换为字符串
      }
      this.emailModalVisible = true
    },

    handleEmailSubmit() {
      this.$refs.emailFormRef.validate(valid => {
        if (valid) {
          // 在提交前，确保 reports 数组中的 ID 都是字符串
          const emailData = {
            ...this.emailForm,
            reports: this.emailForm.reports ? this.emailForm.reports.map(id => String(id)) : []
          }

          this.loading = true
          if (this.emailFormMode === 'add') {
            apiClient.post('/emails', emailData)
              .then(response => {
                this.$message.success('邮箱添加成功')
                this.emailModalVisible = false
                this.fetchEmails()
              })
              .catch(error => {
                console.error('添加邮箱失败:', error)
                let errorMsg = '添加邮箱失败'
                if (error.response && error.response.data && error.response.data.error) {
                  errorMsg = error.response.data.error
                } else if (error.message) {
                  errorMsg = `添加邮箱失败: ${error.message}`
                }
                this.$message.error(errorMsg)

                if (error.message && error.message.includes('Network Error')) {
                  this.$message.error('网络错误: 请确保后端服务器已启动并且可以访问')
                  console.error('建议: 请检查后端服务器是否已启动，并尝试访问 http://localhost:5002/test')
                }
              })
              .finally(() => {
                this.loading = false
              })
          } else {
            apiClient.put(`/emails/${this.emailForm.id}`, emailData)
              .then(response => {
                this.$message.success('邮箱更新成功')
                this.emailModalVisible = false
                this.fetchEmails()
              })
              .catch(error => {
                console.error('更新邮箱失败:', error)
                let errorMsg = '更新邮箱失败'
                if (error.response && error.response.data && error.response.data.error) {
                  errorMsg = error.response.data.error
                } else if (error.message) {
                  errorMsg = `更新邮箱失败: ${error.message}`
                }
                this.$message.error(errorMsg)

                if (error.message && error.message.includes('Network Error')) {
                  this.$message.error('网络错误: 请确保后端服务器已启动并且可以访问')
                  console.error('建议: 请检查后端服务器是否已启动，并尝试访问 http://localhost:5002/test')
                }
              })
              .finally(() => {
                this.loading = false
              })
          }
        }
      })
    },

    deleteEmail(id) {
      this.deleteTargetId = id
      this.deleteDialogVisible = true
    },

    handleConfirmDelete() {
      if (!this.deleteTargetId) return

      this.loading = true
      apiClient
        .delete(`/emails/${String(this.deleteTargetId)}`)
        .then((response) => {
          this.$message.success('邮箱删除成功')
          this.fetchEmails()
        })
        .catch((error) => {
          console.error('删除邮箱失败:', error)
          let errorMsg = '删除邮箱失败'
          if (error.response && error.response.data && error.response.data.error) {
            errorMsg = error.response.data.error
          } else if (error.message) {
            errorMsg = `删除邮箱失败: ${error.message}`
          }
          this.$message.error(errorMsg)

          if (error.message && error.message.includes('Network Error')) {
            this.$message.error('网络错误: 请确保后端服务器已启动并且可以访问')
            console.error('建议: 请检查后端服务器是否已启动，并尝试访问 http://localhost:5002/test')
          }
        })
        .finally(() => {
          this.loading = false
          this.deleteDialogVisible = false
          this.deleteTargetId = null
        })
    },

    handleCancelDelete() {
      this.deleteDialogVisible = false
      this.deleteTargetId = null
    },

    fetchReportOptions() {
      apiClient.get('/report-options')
        .then(response => {
          this.reportOptions = response.data
        })
        .catch(error => {
          console.error('获取报表选项失败:', error)
          this.$message.error('获取报表选项失败')
        })
    },

    // 邮箱组管理方法
    fetchGroups() {
      this.loading = true
      apiClient.get('/email-groups')
        .then(response => {
          this.groupList = response.data
          // 更新分组选项
          this.groupOptions = this.groupList.map(item => ({
            value: item.id,
            label: item.name
          }))
          this.loading = false
        })
        .catch(error => {
          console.error('获取邮箱组列表失败:', error)
          this.$message.error('获取邮箱组列表失败')
          this.loading = false
        })
    },

    searchGroups() {
      this.loading = true
      apiClient.get(`/email-groups/search?q=${this.groupSearchText}`)
        .then(response => {
          this.groupList = response.data
          this.loading = false
        })
        .catch(error => {
          console.error('搜索邮箱组失败:', error)
          this.$message.error('搜索邮箱组失败')
          this.loading = false
        })
    },

    showGroupModal() {
      this.groupFormMode = 'add'
      this.groupForm = {
        id: null,
        name: '',
        members: []
      }
      this.groupModalVisible = true
    },

    editGroup(row) {
      this.groupFormMode = 'edit'
      this.groupForm = {
        id: row.id,
        name: row.group_name, // 修改这里
        members: [] // 这里需要获取当前组的成员
      }

      // 获取当前组的成员
      apiClient.get(`/email-groups/${row.id}/members`)
        .then(response => {
          this.groupForm.members = response.data.map(item => item.id)
          this.groupModalVisible = true
        })
        .catch(error => {
          console.error('获取组成员失败:', error)
          this.$message.error('获取组成员失败')
        })
    },

    handleGroupSubmit() {
      this.$refs.groupFormRef.validate(valid => {
        if (valid) {
          this.loading = true
          if (this.groupFormMode === 'add') {
            // 添加邮箱组API调用
            apiClient.post('/email-groups', this.groupForm)
              .then(response => {
                this.$message.success('邮箱组添加成功')
                this.groupModalVisible = false
                this.fetchGroups()
              })
              .catch(error => {
                console.error('添加邮箱组失败:', error)
                this.$message.error(error.response?.data?.error || '添加邮箱组失败')
              })
              .finally(() => {
                this.loading = false
              })
          } else {
            // 更新邮箱组API调用
            apiClient.put(`/email-groups/${this.groupForm.id}`, this.groupForm)
              .then(response => {
                this.$message.success('邮箱组更新成功')
                this.groupModalVisible = false
                this.fetchGroups()
              })
              .catch(error => {
                console.error('更新邮箱组失败:', error)
                this.$message.error(error.response?.data?.error || '更新邮箱组失败')
              })
              .finally(() => {
                this.loading = false
              })
          }
        }
      })
    },

    deleteGroup(id) {
      // 显示确认对话框
      this.currentGroupId = id
      this.groupDeleteConfirmVisible = true
    },

    // 邮箱组成员管理
    manageGroupMembers(group) {
      this.currentGroupId = group.id

      // 获取所有邮箱
      apiClient.get('/emails')
        .then(response => {
          this.allEmails = response.data.map(item => ({
            id: String(item.id), // 将 id 转换为字符串
            email: item.email
          }))

          // 获取当前组的成员
          return apiClient.get(`/email-groups/${group.id}/members`)
        })
        .then(response => {
          this.selectedEmailIds = response.data.map(item => String(item.id))
          this.memberModalVisible = true
        })
        .catch(error => {
          console.error('获取邮箱或组成员失败:', error)
          this.$message.error('获取邮箱或组成员失败')
        })
    },

    handleMemberChange(value, direction, movedKeys) {
      console.log(value, direction, movedKeys)
    },

    handleMemberSubmit() {
      this.loading = true
      // 保存邮箱组成员变更, 确保ID是字符串
      apiClient.put(`/email-groups/${String(this.currentGroupId)}/members`, {
        memberIds: this.selectedEmailIds.map(id => String(id))
      })
        .then(response => {
          this.$message.success('邮箱组成员更新成功')
          this.memberModalVisible = false
          this.fetchGroups()
        })
        .catch(error => {
          console.error('更新邮箱组成员失败:', error)
          this.$message.error(error.response?.data?.error || '更新邮箱组成员失败')
        })
        .finally(() => {
          this.loading = false
        })
    },

    // 查看全部成员
    viewAllMembers(group) {
      this.currentGroupMembers = group.memberEmails
      this.allMembersVisible = true
    },

    // 邮箱组删除确认
    cancelGroupDelete() {
      this.groupDeleteConfirmVisible = false
      this.currentGroupId = null
    },

    confirmGroupDelete() {
      this.loading = true
      apiClient
        .delete(`/email-groups/${String(this.currentGroupId)}`)
        .then((response) => {
          this.$message.success('邮箱组删除成功')
          this.memberModalVisible = false
          this.fetchGroups()
        })
        .catch((error) => {
          console.error('删除邮箱组失败:', error)
          // 改进错误处理，更详细地输出错误信息
          let errorMsg = '删除邮箱组失败'
          if (error.response && error.response.data && error.response.data.error) {
            errorMsg = error.response.data.error
          } else if (error.message) {
            errorMsg = `删除邮箱组失败: ${error.message}`
          }
          this.$message.error(errorMsg)

          // 检查是否是网络错误
          if (error.message && error.message.includes('Network Error')) {
            this.$message.error('网络错误: 请确保后端服务器已启动并且可以访问')
            console.error('建议: 请检查后端服务器是否已启动，并尝试访问 http://localhost:5002/test')
          }
        })
        .finally(() => {
          this.loading = false
          this.groupDeleteConfirmVisible = false
          this.currentGroupId = null
        })
    }
  }
}
</script>

<style scoped>
.email-container {
  padding: 20px;
}

.email-card {
  margin-bottom: 20px;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.delete-btn {
  color: #f56c6c;
}

.el-transfer {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.member-emails-container {
  display: flex;
  align-items: center;
  width: 100%;
}

.member-emails-wrapper {
  display: flex;
  flex-wrap: nowrap;
  overflow: hidden;
  white-space: nowrap;
  max-width: calc(100% - 80px);
}

.member-email-tag {
  margin-right: 5px;
  flex-shrink: 0;
}

.show-all-btn {
  margin-left: 8px;
}

.all-members-list {
  display: flex;
  flex-wrap: wrap;
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
