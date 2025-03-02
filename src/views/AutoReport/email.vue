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
                <el-popconfirm
                  title="确定要删除此邮箱吗?"
                  @confirm="deleteEmail(scope.row.id)"
                >
                  <el-button
                    slot="reference"
                    type="text"
                    size="small"
                    class="delete-btn"
                  >删除</el-button>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>

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
            v-loading="loading"
            :data="groupList"
            border
            style="width: 100%"
          >
            <el-table-column prop="name" label="组名称" min-width="150" />
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
                <el-popconfirm
                  title="确定要删除此邮箱组吗?"
                  @confirm="deleteGroup(scope.row.id)"
                >
                  <el-button
                    slot="reference"
                    type="text"
                    size="small"
                    class="delete-btn"
                  >删除</el-button>
                </el-popconfirm>
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
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'EmailManagement',
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
      allEmailOptions: []
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
      // 模拟API调用
      setTimeout(() => {
        this.emailList = [
          {
            id: 1,
            email: 'user1@example.com',
            groups: [
              { value: 1, label: '管理组' },
              { value: 2, label: '技术组' }
            ],
            reports: [
              { id: 1, name: '日报' },
              { id: 2, name: '周报' }
            ]
          },
          {
            id: 2,
            email: 'user2@example.com',
            groups: [
              { value: 1, label: '管理组' }
            ],
            reports: [
              { id: 1, name: '日报' }
            ]
          },
          {
            id: 3,
            email: 'user3@example.com',
            groups: [
              { value: 3, label: '市场组' }
            ],
            reports: [
              { id: 3, name: '月报' }
            ]
          }
        ]

        // 更新邮箱选项
        this.allEmailOptions = this.emailList.map(item => ({
          id: item.id,
          email: item.email
        }))

        this.loading = false
      }, 500)
    },

    searchEmails() {
      // 实现邮箱搜索功能
      console.log('搜索邮箱:', this.emailSearchText)
      // 调用API进行搜索
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
        id: row.id,
        email: row.email,
        groups: row.groups ? row.groups.map(g => g.value) : [],
        reports: row.reports ? row.reports.map(r => r.id) : []
      }
      this.emailModalVisible = true
    },

    handleEmailSubmit() {
      this.$refs.emailFormRef.validate(valid => {
        if (valid) {
          // 提交表单逻辑
          if (this.emailFormMode === 'add') {
            // 添加邮箱API调用
            console.log('添加邮箱:', this.emailForm)
          } else {
            // 更新邮箱API调用
            console.log('更新邮箱:', this.emailForm)
          }
          this.emailModalVisible = false
          this.fetchEmails()
        }
      })
    },

    deleteEmail(id) {
      // 删除邮箱API调用
      console.log('删除邮箱ID:', id)
      this.fetchEmails()
    },

    fetchReportOptions() {
      // 获取报表选项
      this.reportOptions = [
        { id: 1, name: '日报' },
        { id: 2, name: '周报' },
        { id: 3, name: '月报' },
        { id: 4, name: '季报' },
        { id: 5, name: '年报' }
      ]
    },

    // 邮箱组管理方法
    fetchGroups() {
      this.loading = true
      // 模拟API调用
      setTimeout(() => {
        this.groupList = [
          {
            id: 1,
            name: '管理组',
            memberCount: 11,
            memberEmails: ['何博凯', '何沛贤', '胡康诚', '白晓圆', '詹翼翔', '何博凯', '何博凯', '何博凯', '何博凯', '何博凯', '显示全部']
          },
          {
            id: 2,
            name: '技术组',
            memberCount: 4,
            memberEmails: ['tech1@example.com', 'tech2@example.com', 'tech3@example.com', 'tech4@example.com']
          },
          {
            id: 3,
            name: '市场组',
            memberCount: 2,
            memberEmails: ['marketing1@example.com', 'marketing2@example.com']
          }
        ]

        // 更新分组选项
        this.groupOptions = this.groupList.map(item => ({
          value: item.id,
          label: item.name
        }))

        this.loading = false
      }, 500)
    },

    searchGroups() {
      // 实现邮箱组搜索功能
      console.log('搜索邮箱组:', this.groupSearchText)
      // 调用API进行搜索
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
        name: row.name,
        members: [] // 这里应该获取当前组的成员ID列表
      }
      this.groupModalVisible = true
    },

    handleGroupSubmit() {
      this.$refs.groupFormRef.validate(valid => {
        if (valid) {
          // 提交表单逻辑
          if (this.groupFormMode === 'add') {
            // 添加邮箱组API调用
            console.log('添加邮箱组:', this.groupForm)
          } else {
            // 更新邮箱组API调用
            console.log('更新邮箱组:', this.groupForm)
          }
          this.groupModalVisible = false
          this.fetchGroups()
        }
      })
    },

    deleteGroup(id) {
      // 删除邮箱组API调用
      console.log('删除邮箱组ID:', id)
      this.fetchGroups()
    },

    // 邮箱组成员管理
    manageGroupMembers(group) {
      this.currentGroupId = group.id
      // 获取所有邮箱
      this.allEmails = this.emailList.map(item => ({
        id: item.id,
        email: item.email
      }))

      // 获取当前组的成员
      // 这里应该调用API获取当前组的成员ID列表
      // 模拟数据
      this.selectedEmailIds = [1, 3] // 假设ID为1和3的邮箱已在组内

      this.memberModalVisible = true
    },

    handleMemberChange(value, direction, movedKeys) {
      console.log(value, direction, movedKeys)
    },

    handleMemberSubmit() {
      // 保存邮箱组成员变更
      // 调用API更新组成员
      console.log('更新邮箱组成员:', {
        groupId: this.currentGroupId,
        memberIds: this.selectedEmailIds
      })
      this.memberModalVisible = false
      this.fetchGroups()
    },

    // 查看全部成员
    viewAllMembers(group) {
      this.currentGroupMembers = group.memberEmails
      this.allMembersVisible = true
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
